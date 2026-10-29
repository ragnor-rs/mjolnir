#!/usr/bin/env python3
"""Hold this repository to naming no other project.

The convention is that nothing here names another project -- no repository slug,
tracker identifier, host path or address -- and that nothing under a carrier root
carries a *value*, where the procedure must read one from configuration instead.
The acceptance item for that convention says the **search is the check**, rather
than a reading of the procedure, so this script is the search and the gate runs
it.

Most of the checks here are of the *forbidding* kind, which is sound only when
the thing forbidden has a stable form; the computed ones -- that the strict set
is swept at all, and that no carrier escapes it -- exist to stop the rest holding
nothing. ⛔ No count of either group is written here: the first form of this
sentence carried one, and the check this file grew next made it wrong. Two rules
keep the forbidding kind sound:

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

# The surface's own reader, imported rather than re-implemented. What the surface
# *publishes* is stated in markers this repository already has exactly one parser
# for, and a second parser here would be the defect this whole gate exists to
# delete: two readings of one surface, each allowed to disagree with it.
#
# ⚠️ The path is derived from this file's own location, so a run from a worktree
# reads that tree's reader rather than the primary checkout's -- the failure that
# otherwise prints a convincing verdict about a file nobody is editing.
_PLUGIN_SCRIPTS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "plugins", "mjolnir", "scripts",
)
if _PLUGIN_SCRIPTS not in sys.path:
    sys.path.insert(0, _PLUGIN_SCRIPTS)

import config as reader  # noqa: E402
import yaml  # noqa: E402 -- a dependency `reader` already states and refuses without

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

# The same distinction, keyed on what the file *is* rather than on which root its
# carrier sits in: a script a carrier calls is implementation under every carrier
# root, not only under this plugin's. Derived from the shapes above so a new
# carrier root inherits it with no second list to keep in step -- the reason
# `STRICT_SHAPES` is built by shape in the first place.
#
# ⛔ A hook is **not** implementation. A hook is the carrier: it is what runs, so
# it is instructions and it is swept. So is a carrier's own file.
#
# ⚠️ What this lets through, stated rather than discovered: a script here may name
# a status word. Measured on a backlog script whose two configured statuses were
# `open` and `closed` -- which are also the two spellings the host uses for the
# same fact, `Issue.closed` in its schema and `OPEN`/`CLOSED` in its state enum.
# No spelling of that query satisfies the value rule, and reading the name out of
# the configuration does not help, because the literal is the host's field name
# rather than a value the script chose. The tree-wide checks still hold every one
# of these files: no home directory, no address, no other repository, no tracker
# identifier.
CARRIER_IMPLEMENTATION = [f"{shape}*/scripts/" for shape in STRICT_SHAPES]

# ⚠️ This file alone, not all of `tools/`. It necessarily writes down every token
# it forbids -- its own grammars and its planted violations contain home paths,
# addresses and foreign slugs. Its sibling needs no such exemption and is swept
# like any other file.
SELF_FILE = "tools/check_no_project_names.py"

# A foreign slug permitted by name, with its reason and the roots it is
# permitted in. The convention forbids naming another *project*; a public
# artifact cited as evidence is not one, and each citation here is load-bearing.
# No count of the entries is written in this comment: the first version of it
# said "one entry" and was wrong the moment a second was added -- in the very
# change that updated both *document* copies of the same fact, which is the
# asymmetry this file's docstring predicts, since nothing holds a comment to a
# document.
#
# ⛔ Each entry names where it is permitted, because a slug permitted everywhere
# is a hole the size of the tree. `docs/` is where this repository quotes the
# measurements it was derived from and the README is where it points at them;
# those are the only places a cited artifact's slug has business appearing.
# Permitting one in a carrier root, in an example configuration or as a `repo:`
# value would let the thing this check exists to catch through under cover of a
# citation. Measured: before the scope existed, the second entry's slug passed
# in a skill and as a `repo:` value in an example.
CITED_ARTIFACTS = {
    "nesquikm/dev-process-toolkit": (
        "the public MIT plugin cited as prior art -- independent confirmation of "
        "the status design",
        ["docs/", "README.md"],
    ),
    "humanlayer/advanced-context-engineering-for-coding-agents": (
        "the published practice § 11's window-as-a-resource measurements are "
        "drawn from",
        ["docs/", "README.md"],
    ),
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

# A machine named by its address. ⛔ The one identity shape of a *machine* with a
# form stable enough for the forbidding kind: a hostname is any word and an alias
# is any word somebody chose, so neither is reachable by a pattern at all --
# which is why `schema.md § 21` keeps the names a guard clears a call with in a
# file outside every working tree rather than holding them with a sweep. What
# this catches is the one spelling that cannot be anything else.
#
# ⚠️ Matched anywhere rather than in a value position, unlike the tracker
# identifiers above: four dotted numbers is not the shape of a version, an
# encoding or a standard's number, so the false-red direction rule 2 exists for
# is not open here. Measured before taking it: the tree carried none.
#
# ⚠️ The trailing guard forbids a *fifth* number rather than any dot: written as
# a plain `(?![\w.])` it let an address at the end of a sentence through, the
# full stop after it being the character it refused — measured, on this check's
# own plant, which is the one state where a forbidding grammar reads as holding
# and holds nothing.
MACHINE_ADDRESS = re.compile(r"(?<![\w.])\d{1,3}(?:\.\d{1,3}){3}(?!\.?\d)")

# Tracker-side identifiers. A Jira key and a Trello object id are matched only in
# a *value* position -- a whole code span, a whole quoted string, or a URL path --
# for the same reason rule 2 exists: `UTF-8`, `SHA-256`, `ISO-8601` and `RFC-7231`
# have a Jira key's exact shape, and a check that reddened on a document naming
# an encoding would be the quoting failure one check over.
TRACKER_IDS_IN_VALUE = [
    (re.compile(r"^[A-Z][A-Z0-9]{1,9}-\d+$"), "a Jira issue key"),
    (re.compile(r"^[0-9a-f]{24}$"), "a Trello object id"),
    # A tracker account id in the **prefixed** spelling, which is the one
    # person-shaped identifier here with a form that cannot be anything else.
    # ⛔ Only the decidable end of schema.md § 27's class is held: a personal name
    # is any word, a handle is any word somebody chose, and -- measured -- a bare
    # dashed hex group is the shape of a *session* id this repository's own
    # fixtures carry, which is nobody. So the first form of this entry made the
    # bare group optional-prefixed and reddened on a suite fixture: the false red
    # rule 2 exists against, reached from the one direction a person-shaped
    # pattern can reach it. ⚠️ What that leaves unheld is stated rather than
    # implied -- a login, a display name and an unprefixed account id are held by
    # § 27 keeping the identities in a file the project points at, never by a
    # sweep, which is `check_no_machine_is_named`'s split one class over.
    (
        re.compile(r"^\d+:[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}$"),
        "a tracker account id, which identifies a person",
    ),
]
TRACKER_IDS_ANYWHERE = [
    (re.compile(r"\b[A-Za-z0-9-]+\.atlassian\.net\b"), "a Jira site"),
    (re.compile(r"\btrello\.com/[bc]/\S+"), "a Trello board or card"),
]

# Asking who is running. ⛔ Each of these is a spelling that resolves *the
# current user* and nothing else, and `schema.md § 27` forbids a role being
# resolved that way: asking the tracker, the host or the shell who you are
# answers who is running the role rather than who holds it, and the check that
# reads the answer silently becomes "assigned to whoever is asking".
#
# ⚠️ Matched **anywhere** in a strict file and not in code regions alone, unlike
# the stack list below. The failure here is a role *instructed* to resolve a
# person that way, which is prose rather than a command. Measured before taking
# it: no file in the strict set carried any of these.
#
# ⛔ **So every spelling here has to be one English does not also use, and the
# hyphenated modifier is not.** The first form of this list separated the two
# words on `[_-]?`, and reproduced both of the failures that costs at once: a
# carrier describing this very rule — *the current-user spelling* — was refused,
# while `--current-user`, the one spelling that cannot be anything but code, went
# unread because the lookbehind rejected the dash in front of it. ⛔ So the
# separator is `_` or nothing, the flag is an entry of its own with its dashes,
# and ⚠️ **the hyphenated English form passes deliberately** — asserted on the
# green side below rather than left to reading.
#
# ⚠️ What this does **not** reach is stated rather than discovered: a role could
# write *ask the tracker who you are* in words, and a sweep for that is a sweep
# for every word. What holds that half is § 27 being the one statement of the
# rule, and the shared reader refusing `current_user` wherever a configuration
# writes it -- which is a refusal with a plant of its own, one script over.
#
# ⛔ No count of these is written here or in the documents that describe this
# check. The first form of all three said *three* and this change's own fix made
# it four, green — which is the failure the group counts above already record.
WHO_AM_I = [
    (re.compile(r"(?<![\w.@])@me(?![\w-])"), "the code host's spelling of the current user"),
    (re.compile(r"(?<![\w-])current_?user(?![\w-])", re.I),
     "a query for the current user"),
    (re.compile(r"(?<!\w)--current-user(?![\w-])", re.I),
     "a flag naming the current user"),
    (re.compile(r"(?<![\w-])whoami(?![\w-])"), "a shell's answer about who is running"),
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

# A stack's own flag, written with its dashes. ⛔ Separate from the list above
# rather than a group of it, because that one is matched on word tokens -- a flag
# tokenises to the bare word, and forbidding `offline` or `fix` as words would
# redden on ordinary prose inside a code span. ⚠️ It is also the arm that was
# missing while a flag was caught only where the command it belongs to was: a
# role writing `--offline` alone tripped nothing, the surface's rule being that
# no stack token appears in a carrier's text rather than no stack *command*.
#
# ⚠️ A closed list, which is the quoting weakness this repository states
# elsewhere, and it errs the same way: a flag nobody wrote down passes and leaves
# a reviewer to catch it, never a false red on a role's own flag. Four of these
# are measured -- the cache-and-daemon pair one project's gating command carries,
# and the two repairing forms another's checks run under -- and the rest are the
# commonest spellings of the same two classes.
STACK_FLAGS = {
    "a build tool's own flag": """
        --offline --no-daemon --no-build-cache --frozen-lockfile --legacy-peer-deps
    """,
    "a flag that makes a command repair what it judges": """
        --fix --write
    """,
}

# A language interpreter. ⛔ On this list in **one position only**: in front of
# something this repository does not itself ship. The surface settles which
# position that is -- a command is stated whole and the procedure supplies no part
# of it, so an interpreter a role prefixes is a guess about the language a
# *configured* script is written in, wrong the first time somebody writes one in
# another language, and the configuration never said so.
#
# ⚠️ So the arm reads what *follows* the interpreter rather than the token, and
# the two positions it lets through are the two where there is no guess: a file
# this repository tracks, whose language the carrier beside it can see, and a
# region where nothing follows the interpreter at all -- the shape a hook carrier
# is in, where the command and its arguments are separate members of a JSON
# object. ⛔ The first of those is computed from the file list rather than
# pattern-matched, which is the strong kind of exemption: a path that stops being
# tracked stops being exempt with no edit here.
INTERPRETERS = {"python", "python3", "node", "deno", "ruby", "perl", "php", "Rscript"}

# The one means a carrier has of naming a file the *plugin* ships: the harness
# substitutes the plugin's own location for it, so the path is not resolvable
# against the file list and is read by this spelling instead. The line it draws is
# the one `PLUGIN_NON_CARRIER` draws one scope over -- the toolkit's own
# implementation is not a project's stack.
PLUGIN_ROOTED = re.compile(r"\$\{?CLAUDE_PLUGIN_ROOT\}?")

# What a path looks like where a command names one. Read against the tracked file
# list, so what is exempt is a file this repository holds and not a shape.
PATH_LIKE = re.compile(r"[\w./-]+")

# ⛔ **An interpreter in front of a *configured* path is permitted nowhere.** No
# role reads a script's location out of configuration -- every one it runs is
# either a file this repository tracks or a file the plugin ships, and each of
# those is resolved above -- so there is no table of exceptions here and an
# instance of the form reddens. ⚠️ **Stated rather than left to the absence of
# code**: a table with no entry and no plant is a branch nothing exercises, which
# is the shape that reports green while it quietly stops working, so what would
# otherwise be an empty exemption is a sentence instead.

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

# Which value a configuration carries is **every scalar it states**, minus the
# vocabulary the surface itself publishes. ⛔ Not a list of the key names those
# values happen to sit under: measured by planting, a configured branch prefix
# and a configured label both passed such a list, and neither is reachable by
# one. The prefix sits under `work_item.type_branch_prefix.<one of the project's
# own types>` -- a key the project itself names -- and the label sits in
# `tracker.labels`, a plural whose singular `label` is a readiness check's
# argument, a different fact one letter away. A list of key names cannot express
# the line, because the project-invented classes sit under keys no list can
# anticipate.
#
# ⚠️ And the line is not "every value the surface writes" either. The surface
# *illustrates* some keys with a concrete value -- `label_prefix: "type:"`,
# `type_branch_prefix: { bug: bugfix }` -- and a project writing the same string
# has still invented it. What the surface **publishes** is narrower and marked:
#
# - a closed alternation, `kind: worktree | in_place`, in either of the two
#   shapes the surface writes one;
# - a value marked `# default`.
#
# Both are read through `reader.surface_facts`, so a facet added to the surface
# changes what this sweep forbids with no edit here -- the property this script
# already claims for its other reads. ⛔ Which is also why `worktree`, `in_place`
# and `explicit` must stay nameable: § 6's dirty-tree derivation and § 10's
# routing table are stated *by mode*, so a role forbidden from saying `worktree`
# could not name § 10 at all.
#
# ⚠️ A number, a flag and a null are nobody's vocabulary and are not read at all;
# what that leaves unguarded is in the document the docstring names.

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
# The delimiter of a ``…`` span, split on rather than paired. ⛔ Not a regex, and
# for the reason stated against fenced blocks in `code()`: a paired form matches
# one span's closer against the next span's opener, so a single unbalanced
# occurrence swallows everything between the two and every value in there stops
# being read as a value -- the failure mode being hidden coverage rather than a
# false red. Splitting makes an unclosed delimiter inert instead: its text stays
# outside, and only a balanced pair takes anything out.
DOUBLE_SPAN_DELIMITER = "``"
QUOTED_ANY = re.compile(r"\"([^\"]*)\"|«([^»]*)»|“([^”]*)”")
QUOTED_SINGLE = re.compile(r"'([^']*)'")

# ⛔ A key of a JSON object is structure, not a value, and in JSON a key is
# necessarily quoted -- so rule 2's "whole quoted string" reads every key of
# every carrier written in that format as a value. The live instance is the hook
# carrier: `"hooks"` is the harness's own schema word three times over, and this
# project happens to classify work with a label of the same spelling. ⚠️ Scoped to
# `.json` by extension and to nothing else: in a script a quoted key is a dict
# literal's, where the value beside it is the thing worth sweeping, and widening
# this would exempt a value written as a key. A JSON *value* is swept, which is
# one of the planted violations.
JSON_KEY = re.compile(r"\"([^\"]*)\"\s*:")

# Two characters is a real value -- a tracker's `CI`, a label prefix's `E:`.
MIN_VALUE_LEN = 2

SHEBANG = re.compile(r"^#!.*$", re.M)
TRAILING_COMMENT = re.compile(r"(?<!\\)#.*$")


def _tokens(groups: dict[str, str]) -> list[tuple[str, str]]:
    return [(token, label) for label, blob in groups.items() for token in blob.split()]


def _leaves(node, keys: tuple[str, ...] = ()):
    """Every scalar a parsed document states, with the key path it sits under.

    ⛔ A list's members are leaves of their own. A key whose value is a list
    carries as many of a project's facts as it has members, and reading the whole
    bracket as one string forbids a value no carrier could ever contain -- which
    reads as a check doing its job and is a check holding nothing. ⚠️ Measured on
    § 14's `inherits`, where a line-based read stops at the first comma and yields
    `[PATH`: every real member of the list goes unswept while the key reads as
    covered, which is the whole of the failure.

    ⚠️ A list's members carry the *list's* path and no index, which is what lets
    the subset test below ask about the list they came from.
    """
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _leaves(value, keys + (str(key),))
    elif isinstance(node, list):
        for item in node:
            yield from _leaves(item, keys)
    else:
        yield keys, node


def _list_nodes(node, keys: tuple[str, ...] = ()):
    """Each list a document states, with its scalar members -- for the subset test."""
    if isinstance(node, dict):
        for key, value in node.items():
            yield from _list_nodes(value, keys + (str(key),))
    elif isinstance(node, list):
        yield keys, [str(i) for i in node if not isinstance(i, (dict, list))]
        for item in node:
            yield from _list_nodes(item, keys)


def _scalars(value) -> list[str]:
    """Each scalar inside a value the surface states, a list's members included."""
    if isinstance(value, dict):
        return [s for item in value.values() for s in _scalars(item)]
    if isinstance(value, (list, tuple)):
        return [s for item in value for s in _scalars(item)]
    return [str(value)]


def _inline_list(rest: str) -> list[str] | None:
    """The members of an inline list a surface key states, or None.

    The surface writes a closed vocabulary two ways: as an alternation, which the
    reader already returns, and as a list -- § 9's `streams` is the live
    instance. A list is read here rather than in the reader because nothing else
    needs it yet, and ⛔ it is read through the reader's own fence and key walk, so
    the markdown is parsed once however many facts are taken out of it.
    """
    value = rest.split("#")[0].strip()
    if not (value.startswith("[") and value.endswith("]")):
        return None
    try:
        members = yaml.safe_load(value)
    except yaml.YAMLError:
        return None
    return [str(m) for m in members] if isinstance(members, list) else None


STACK = _tokens(STACK_TOKENS)

# Each flag as a whole token, dashes included. The right-hand boundary forbids a
# word or a further dash after it, so `--fix` does not match `--fixture`; the
# left-hand one forbids a word character, so a flag written as the tail of a
# longer one is still its own token.
STACK_FLAG = [
    (re.compile(rf"(?<![\w-]){re.escape(flag)}(?![\w-])"), what)
    for flag, what in _tokens(STACK_FLAGS)
]

# The interpreter as the head of what it prefixes. ⚠️ Matched anywhere in a
# region rather than only at its start: a region is one line of a fenced block or
# one code span, and the interpreter in the live instances sits after a prompt,
# a key or a pipe as often as at the head.
INTERPRETER = re.compile(
    r"(?<![\w./-])(?:" + "|".join(sorted(map(re.escape, INTERPRETERS))) + r")(?![\w-])"
)


def rooted_at_procedure_command(region: str) -> bool:
    """Is this command's own name `git` or `gh`?"""
    head = region.strip().split()
    return bool(head) and head[0] in PROCEDURE_COMMANDS


def deslugged(name: str) -> re.Pattern[str]:
    """`github-projects` also written `GitHub Projects`, or `githubprojects`.

    A tracker's name reaches the surface as a `kind:` slug and reaches prose as
    words. Matching only the slug would certify the check on the one spelling
    nobody writes.

    ⛔ A hyphen or an underscore beside the name does **not** protect it. The
    first form put `-` in both lookarounds, so `trello-sync`, `sync-trello` and
    `trello_sync` all passed -- and a carrier is named in exactly that shape,
    which is the one place this check looks. The word boundary is the word's,
    so a compound naming a tracker names it.

    ⚠️ `_` is spelled out rather than left to `\\w`, which contains it: the
    second form of this pattern closed the hyphen hole and left the underscore
    one open, measured by planting both.
    """
    boundary = "[0-9A-Za-z]"
    return re.compile(
        f"(?<!{boundary})"
        + r"[-\s]?".join(map(re.escape, name.split("-")))
        + f"(?!{boundary})"
    )


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
            and not self.inside(p, CARRIER_IMPLEMENTATION)
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
                # ⛔ Both paths, for the reason the fence toggle is in both: a
                # ``…`` span's backticks are not a span's delimiters, so leaving
                # them in pairs them with the ones after and a real code span
                # stops being read as one.
                regions.extend(CODE_SPAN.findall(self._spans_out(line, regions)))
        return regions

    @staticmethod
    def _spans_out(text: str, out: list[str]) -> str:
        """Take every ``…`` span out, and sweep what is inside it as well.

        Returns what is left, so the single-backtick pass runs on text whose
        backticks all pair the way the document means them to.

        ⛔ **Split, never paired.** For the reason stated against fenced blocks
        in `code()`: a paired form matches one span's closer against the next
        span's opener, so a single unbalanced occurrence swallows every value
        between the two and the sweep goes quiet over it. Splitting makes an
        unclosed delimiter inert -- its text stays outside, where it is read.

        ⛔ **And the inside is swept, not just collected.** This repository's own
        idiom for showing a literal span is a ``…`` around one, so taking the
        span out without reading into it hides exactly the values most likely to
        be written there. Measured: ``…`In Progress`…`` passed while the same
        value in a plain span reddened.
        """
        parts = text.split(DOUBLE_SPAN_DELIMITER)
        balanced = (len(parts) - 1) % 2 == 0
        kept = [parts[0]]
        for index, part in enumerate(parts[1:], start=1):
            # Odd segments are inside a span -- except a final odd one where the
            # delimiters do not pair, which is not a span at all.
            if index % 2 and (balanced or index != len(parts) - 1):
                out.append(part.strip())
                out += CODE_SPAN.findall(part)
            else:
                kept.append(part)
        return " ".join(kept)

    def value_contexts(self, path: str) -> list[str]:
        """Whole spans and whole quoted strings, per rule 2.

        ⛔ Fenced blocks come out first, by the same line toggle `code` uses. A
        fence's own backticks otherwise shift the pairing of every span after it,
        so a value written as a span lands inside a span the document never had.
        A line of a fence is a context in its own right.

        ⛔ ``…`` spans come out next, for exactly that reason one level down:
        they are the other construct whose backticks are not a span's
        delimiters. ⚠️ **Markdown only**, like the fence toggle above and for the
        same reason — a double backtick is a markdown construct. In a script the
        two halves of a `"```"` literal pair with each other across hundreds of
        unrelated lines, and taking that region out blinds the sweep over it:
        measured at 722 lines of one module, with a planted tracker key inside
        it going unreported.
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
            flat = self._spans_out(flat, out)
            out += CODE_SPAN.findall(flat)
            out += [g for match in QUOTED_ANY.finditer(flat) for g in match.groups() if g is not None]
            return out
        out = [line.strip() for line in body.splitlines()]
        out += CODE_SPAN.findall(body)
        keys = {match.start() for match in JSON_KEY.finditer(body)} if path.endswith(".json") \
            else set()
        for pattern in (QUOTED_ANY, QUOTED_SINGLE):
            out += [
                g for match in pattern.finditer(body)
                if match.start() not in keys
                for g in match.groups() if g is not None
            ]
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

    def published_vocabulary(self) -> tuple[set[str], dict[str, set[str]], list[str]]:
        """What the surface publishes: (every member, its closed lists, problems).

        ⛔ Published, never merely written. The alternations and the marked
        defaults come from the surface's own reader; the lists are walked here
        through that reader's fence and key walk. Everything else a fence shows is
        an *illustration* of a project's fact and is not subtracted -- which is
        the whole of why a configured branch prefix is caught while `worktree` is
        not.

        ⚠️ A surface this reader cannot read is reported rather than treated as a
        surface that publishes nothing: with an empty set every value a
        configuration states reads as that project's own, which floods instead of
        hiding, but the sweep would then be measuring its own copy of nothing.
        """
        text = self.text.get(SURFACE, "")
        try:
            facts = reader.surface_facts(text)
        except (reader.ConfigError, yaml.YAMLError) as exc:
            return set(), {}, [
                f"{SURFACE}: the surface's own reader cannot read what it publishes — "
                f"{exc}. This check subtracts the published vocabulary from every value a "
                "configuration states, and that subtraction is not happening."
            ]
        pool = {member for members in facts["enums"].values() for member in map(str, members)}
        for value in facts["defaults"].values():
            pool.update(_scalars(value))
        lists: dict[str, set[str]] = {}
        for _heading, block in reader._fences(text):
            for path, rest in reader._walk_keys(block):
                members = _inline_list(rest)
                if members is not None:
                    lists.setdefault(path.split(".")[-1], set()).update(members)
        return pool, lists, []

    def configuration_values(self) -> tuple[dict[str, str], list[str]]:
        """(value -> the configuration and key path it came from, problems).

        Every scalar a configuration states is that project's own vocabulary
        unless the surface publishes it. ⛔ The problems are returned beside the
        values rather than raised, because each of them is a way for this check to
        hold nothing while reporting green: a surface that publishes nothing, a
        configuration that does not parse, a configuration that states no value at
        all. ⚠️ There is no list of key names to go stale -- a key renamed anywhere
        is still a leaf and still read -- so these three arms are the whole of
        this check's self-guard.
        """
        pool, published_lists, problems = self.published_vocabulary()
        own = self.own_slug()
        found: dict[str, str] = {}
        for path in self.configs():
            try:
                document = yaml.safe_load(self.text.get(path, "")) or {}
            except yaml.YAMLError as exc:
                problems.append(
                    f"{path}: does not parse as a configuration, so every value it states "
                    f"is read as no value at all and the sweep goes quiet over the file "
                    f"— {exc.__class__.__name__}."
                )
                continue
            in_data = self.inside(path, DATA_ROOTS)
            # A list whose every member the surface publishes under the same key
            # is a choice from the surface's own words rather than a vocabulary
            # this project invented. ⛔ One member the surface does not publish
            # makes the whole list the project's -- which is what keeps a type
            # vocabulary forbidden, that being a list of a project's own words
            # under the very same shape.
            closed = {
                keys for keys, members in _list_nodes(document)
                if members and set(members) <= published_lists.get(keys[-1] if keys else "", set())
            }
            stated = 0
            for keys, value in _leaves(document):
                if not isinstance(value, str):
                    continue
                value = value.strip()
                if not value or value == own or value in pool or keys in closed:
                    continue
                if len(value) < MIN_VALUE_LEN and not value.endswith(":"):
                    continue
                if PLACEHOLDER.match(value):
                    continue
                if in_data and PLACEHOLDER_IN_DATA.match(value):
                    continue
                stated += 1
                found.setdefault(value, f"{path} ({'.'.join(keys)})")
            if not stated:
                problems.append(
                    f"{path}: states no concrete value of its own, so this check has nothing "
                    "to look for from it. The examples are placeholders by design, but at "
                    "least one concrete status word, workflow name or heading per "
                    "configuration is what gives the sweep something to sweep for."
                )
        return found, problems

    def forbidden_values(self) -> dict[str, str]:
        """Every value a configuration states as its own. What the plants read."""
        return self.configuration_values()[0]


# --- the checks ------------------------------------------------------------


def check_no_other_repository_is_named(tree: Tree) -> list[str]:
    own = tree.own_slug()
    problems = []
    if not own:
        return [
            f"{OWN_CONFIG}: states no `host.repo`, so this check has no permitted slug to "
            "measure against and would forbid every slug including this project's own."
        ]
    for path in tree.everything():
        body = tree.text[path]
        found = [(m.group("slug"), "a code-host URL") for m in HOST_URL.finditer(body)]
        found += [(m.group("slug"), "an install command") for m in MARKETPLACE_SLUG.finditer(body)]
        if path in tree.configs():
            found += [(m.group("slug"), "a `repo:` value") for m in CONFIG_SLUG.finditer(body)]
        for slug, form in found:
            if slug == own:
                continue
            cited = CITED_ARTIFACTS.get(slug)
            if cited and tree.inside(path, cited[1]):
                continue
            if tree.inside(path, DATA_ROOTS) and PLACEHOLDER_IN_DATA.match(slug):
                continue
            scope = (
                f" It is a cited artifact -- {cited[0]} -- and is permitted only in "
                f"{', '.join(cited[1])}."
                if cited
                else ""
            )
            problems.append(
                f"{path}: names the repository `{slug}` as {form}. This repository names no "
                f"other project's slug; the permitted ones are `{own}`, its own, and the "
                f"cited-artifact table in this script, each within the roots it names.{scope}"
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


def check_no_machine_is_named(tree: Tree) -> list[str]:
    """No machine is named by its address, anywhere in the tree.

    The convention's own words for the class are `schema.md § 21`'s: no host,
    alias, user, jump path or fingerprint enters this toolkit. ⛔ **Only the
    decidable end of that is held here** -- an address, which cannot be anything
    else -- and the rest is held by where the names live rather than by a
    pattern: a sweep for a hostname is a sweep for every word.
    """
    problems = []
    for path in tree.everything():
        for match in MACHINE_ADDRESS.finditer(tree.text[path]):
            line = tree.text[path].count("\n", 0, match.start()) + 1
            problems.append(
                f"{path}:{line}: names the machine at `{match.group(0)}`. A machine's address is "
                "a project's fact wherever it is written, and the guard that holds a session "
                "reads its names from a file outside every working tree."
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


# An exception, encoded rather than assumed, and the narrowest of them. ⚠️ No ordinal: the first
# form of this comment said *fourth* and a fifth entry landed beside it, green.
#
# A carrier-classification map is keyed by the basenames projects actually gave
# their carriers, and a project that named a hook after its build tool is a fact
# such a map has to carry: dropping the key makes the role it classifies read as
# a role that does not exist, which is the one error that check must not make.
# ⛔ It is the KEY that is exempt and not the file, and not the value beside it:
# a line that does anything but map a name to a classification is swept like any
# other. The map itself is data about other projects, in the sense
# `config/examples/` is data rather than procedure.
CARRIER_MAP_KEY = re.compile(r"^(?P<key>[A-Za-z0-9_.-]+):\s*\{[^}]*\b(?:role|class|partial)\b")


def carrier_name_exception(path: str, region: str, token: str) -> bool:
    """Is this token only in the *key* of a carrier-classification entry?"""
    match = CARRIER_MAP_KEY.match(region.strip())
    if not match:
        return False
    key = match.group("key")
    if token not in re.split(r"[-_]", key) and token != key:
        return False
    return token not in region[match.end("key"):]


def check_no_stack_is_named_in_the_strict_set(tree: Tree) -> list[str]:
    problems = []
    swept = 0
    for path in tree.strict():
        for region in tree.code(path):
            swept += 1
            words = set(re.findall(r"[A-Za-z0-9_.-]+", region))
            # ⛔ And the parts of each one. A token is split on the separators a
            # name is compounded with, because the first form matched whole
            # tokens only and so read straight past a build tool named inside
            # one -- which is the shape a carrier's own name takes. A manifest
            # or lockfile name keeps its dots, so the split is on `-` and `_`.
            words |= {
                part
                for word in words
                for part in re.split(r"[-_]", word)
                if part
            }
            for token, what in STACK:
                if token in words and not carrier_name_exception(path, region, token):
                    problems.append(
                        f"{path}: the command `{region.strip()[:70]}` names {what} "
                        f"(`{token}`). A role reads the command it runs from configuration; a "
                        "role that names one has learned what produced a verdict."
                    )
            for pattern, what in STACK_FLAG:
                found = pattern.search(region)
                if found:
                    problems.append(
                        f"{path}: the command `{region.strip()[:70]}` names {what} "
                        f"(`{found.group(0)}`). A flag is a stack token like the "
                        "command it belongs to, and a flag written into a role is "
                        "read by nobody: what defeats a stale pass is a command "
                        "the project states (schema § 17)."
                    )
            for found in INTERPRETER.finditer(region):
                prefixed = region[found.end():].strip(" \t\"',;:)]}")
                if not prefixed or PLUGIN_ROOTED.search(prefixed):
                    continue
                head = PATH_LIKE.match(prefixed)
                # ⚠️ `removeprefix` and never `lstrip`, which strips every
                # leading `.` and `/` it meets: it turned `.claude/…` into
                # `claude/…`, which is tracked under no name, so every path under
                # the harness's own dotted root read as untracked and reddened.
                if head and head.group(0).removeprefix("./") in tree.text:
                    continue
                problems.append(
                    f"{path}: the command `{region.strip()[:70]}` prefixes "
                    f"`{prefixed[:40]}` with the interpreter `{found.group(0)}`. A "
                    "command is stated whole and the procedure supplies no part of "
                    "it (schema § What the procedure models): an interpreter a "
                    "role writes is a guess about the language a configured script "
                    "happens to be in."
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


def check_no_role_is_resolved_through_the_running_user(tree: Tree) -> list[str]:
    """No carrier resolves who holds a role by asking who is running.

    `schema.md § 27` states the rule and the map a role is looked up in instead.
    ⛔ Scoped to the strict set, and the scope is the rule's own rather than
    forbearance: the implementation behind `assign` legitimately translates the
    running user's spelling, because recording who *took* an item is a fact about
    this run and is a different act from asking who *holds* the role. A sweep that
    reddened on it would forbid the one shape § 27 permits.
    """
    problems = []
    for path in tree.strict():
        body = tree.text[path]
        for pattern, what in WHO_AM_I:
            for match in pattern.finditer(body):
                line = body.count("\n", 0, match.start()) + 1
                problems.append(
                    f"{path}:{line}: names `{match.group(0)}`, which is {what}. A role is "
                    "resolved by identity, looked up in the map a project points at "
                    "(schema § 27): asking who is running answers who is running, and the "
                    "check that reads the answer becomes `assigned to whoever is asking`."
                )
    return problems


def check_no_value_is_carried_in_the_strict_set(tree: Tree) -> list[str]:
    values, problems = tree.configuration_values()
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
    ("no machine is named", check_no_machine_is_named),
    ("no role is resolved through the running user",
     check_no_role_is_resolved_through_the_running_user),
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


def _plant_in_a_carrier_implementation(text: str):
    """Into a script a carrier calls, which is implementation and not swept."""
    def apply(tree: Tree) -> Tree:
        shape = STRICT_SHAPES[0]
        tree.text[f"{shape}planted/scripts/planted.py"] = "#!/usr/bin/env python3\n" + text
        return tree

    return apply


def _plant_in_a_hook(text: str):
    def apply(tree: Tree) -> Tree:
        tree.text["hooks/planted.sh"] = "#!/usr/bin/env bash\n" + text
        return tree

    return apply


def _plant_in_a_json_carrier(text: str):
    """Into a hook carrier written in JSON, where every key is a quoted string."""
    def apply(tree: Tree) -> Tree:
        tree.text["hooks/planted.json"] = text
        return tree

    return apply


def _a_configured(tree: Tree, *keys: str) -> str:
    """A value this project's own configuration states under a key path.

    ⛔ Read out of the configuration rather than written here. A plant carrying
    the literal keeps passing after the project rewords its vocabulary, which is
    a plant asserting its own text; and the value this one must return is exactly
    the one no list of key names could reach.

    ⛔ **And one the derivation forbids**, which is not the same thing. A project
    whose label vocabulary carries a word the surface publishes -- `all` and
    `field` are both one letter from an ordinary label -- hands the plant a value
    that is nameable by design, and the self-test then reports it as having
    stayed green: a false red reading exactly like the sweep regressing.
    Reproduced by planting `all` into this project's own labels.
    """
    node = yaml.safe_load(tree.text.get(OWN_CONFIG, "")) or {}
    for key in keys:
        node = node.get(key) if isinstance(node, dict) else None
    members = sorted(set(_scalars(node))) if node else []
    if not members:
        raise AssertionError(
            f"{OWN_CONFIG} states nothing under `{'.'.join(keys)}`, so this plant tests nothing"
        )
    forbidden = tree.forbidden_values()
    chosen = [member for member in members if member in forbidden]
    if not chosen:
        raise AssertionError(
            f"every value {OWN_CONFIG} states under `{'.'.join(keys)}` is one the surface "
            f"publishes ({', '.join(members)}), so this plant would carry a nameable value "
            "and assert nothing"
        )
    return chosen[0]


def _plant_a_configured_branch_prefix(tree: Tree) -> Tree:
    """The prefix one of a project's own types maps to, planted in a carrier.

    ⛔ The shape is the whole point. `work_item.type_branch_prefix` is a map whose
    *keys* are the project's own type vocabulary, so the prefix sits under a key
    name nothing can anticipate -- measured green against a list of key names,
    and found while writing the starting role, whose text is the one place
    that value must not appear, since reading it from configuration is what that
    role is for.
    """
    prefix = _a_configured(tree, "work_item", "type_branch_prefix")
    return _plant_in_a_carrier(f"\nCut the branch with the `{prefix}` prefix.\n")(tree)


def _plant_a_configured_label(tree: Tree) -> Tree:
    """A label out of the project's own label vocabulary.

    ⛔ The other shape a list of key names cannot reach: `tracker.labels` is a
    plural key holding a list, while the singular `label` is a readiness check's
    argument -- a different fact under a name one letter away, which is how such
    a list reads as covering this and does not.
    """
    label = _a_configured(tree, "tracker", "labels")
    return _plant_in_a_carrier(f"\nThe item carries the `{label}` label.\n")(tree)


def _a_facet_value(tree: Tree, key: str) -> str:
    """A value this project's `host.checks` states under the given key.

    The counterpart of `_a_configured` for § 2's facet, which that function
    cannot reach: `host.checks` is a **list of entries**, so every fact in it
    sits under a key that is a member's and not a path's -- the third shape a
    list of key names cannot express, after the two `_a_configured` records.

    ⛔ Read out of the configuration for that function's reason, and the keys it
    is asked for are the three § 2 names as a consumer's own facts: the workflow
    name a run is keyed by, the trigger pattern that starts it, and the path
    filter it watches. A carrier naming any of them has copied a project's fact
    into the shared procedure, which is what `host_checks.py` exists so that no
    carrier has to do.
    """
    document = yaml.safe_load(tree.text.get(OWN_CONFIG, "")) or {}
    entries = (document.get("host") or {}).get("checks") or []
    members = sorted({
        value
        for entry in entries if isinstance(entry, dict)
        for value in _scalars(entry.get(key)) if entry.get(key) is not None
    })
    if not members:
        raise AssertionError(
            f"{OWN_CONFIG} states no `{key}` on any `host.checks` entry, so this "
            "plant tests nothing"
        )
    forbidden = tree.forbidden_values()
    chosen = [member for member in members if member in forbidden]
    if not chosen:
        raise AssertionError(
            f"every `{key}` {OWN_CONFIG} states is a value the surface publishes "
            f"({', '.join(members)}), so this plant would carry a nameable value "
            "and assert nothing"
        )
    return chosen[0]


def _plant_a_configured_path_filter(tree: Tree) -> Tree:
    """A path filter, stated in the configuration and named in a carrier.

    ⛔ The filter is planted into the configuration as well as into the carrier,
    and that is not a convenience. No workflow in **this** repository filters by
    path, so `host.checks` states no filter and the arm would hold nothing here
    -- a plant that read the live configuration would raise rather than assert,
    and the first adopter whose workflows do filter would be the first to find
    out. Planting both halves asserts the arm for that adopter's tree from this
    one. ⚠️ The glob is a shape no path here has, so it cannot be the value of
    anything else the sweep finds.
    """
    document = yaml.safe_load(tree.text.get(OWN_CONFIG, "")) or {}
    entries = (document.get("host") or {}).get("checks") or []
    if not entries or not isinstance(entries[0], dict):
        raise AssertionError(
            f"{OWN_CONFIG} states no `host.checks` entry to carry a filter, so "
            "this plant tests nothing"
        )
    glob = "a-planted-tree/**"
    entries[0]["paths"] = [glob]
    tree.text[OWN_CONFIG] = yaml.safe_dump(document)
    return _plant_in_a_carrier(f"\nThe run watches `{glob}`.\n")(tree)


def _plant_in_a_named_root(roots: list[str], text: str):
    """Into a strict file inside one of the roots given, synthesised if none.

    The counterpart of `a_strict_file` for an exemption whose entry names the
    roots it holds in: a plant that landed in whichever file sorted first would
    assert the scope of nothing. ⛔ Never a hardcoded path, for `a_strict_file`'s
    own reason -- a renamed carrier root must redden a check rather than kill the
    run with a KeyError in place of a verdict.
    """

    def apply(tree: Tree) -> Tree:
        inside = [
            p for p in sorted(tree.strict())
            if p.endswith(".md") and Tree.inside(p, roots)
        ]
        path = inside[0] if inside else f"{roots[0]}SKILL.md"
        tree.text[path] = tree.text.get(path, "# Planted\n") + text
        return tree

    return apply


def _a_tracked_script(tree: Tree) -> str:
    """A path this repository tracks, for the exemption computed from that list.

    Read out of the file list rather than written here, for the reason the
    configured-value plants read their values out of the configuration: a literal
    would assert its own text, and this exemption's whole claim is that what makes
    a path exempt is the repository holding it.
    """
    for path in sorted(tree.text):
        if path.endswith(".py"):
            return path
    raise AssertionError(
        "this repository tracks no script for an interpreter to be exempt in front "
        "of, so that exemption asserts nothing"
    )


def _a_published_alternation_member(tree: Tree) -> str:
    """A value this project configures that the surface publishes as an alternation."""
    pool, _lists, _problems = tree.published_vocabulary()
    document = yaml.safe_load(tree.text.get(OWN_CONFIG, "")) or {}
    for _keys, value in _leaves(document):
        if isinstance(value, str) and value.strip() in pool and len(value.strip()) >= MIN_VALUE_LEN:
            return value.strip()
    raise AssertionError(
        f"{OWN_CONFIG} configures no value the surface publishes as an alternation, so this "
        "exemption asserts nothing"
    )


def _a_published_list_member(tree: Tree) -> str:
    """A member of a closed list the surface publishes, as this project chose it."""
    _pool, lists, _problems = tree.published_vocabulary()
    document = yaml.safe_load(tree.text.get(OWN_CONFIG, "")) or {}
    for keys, members in _list_nodes(document):
        published = lists.get(keys[-1] if keys else "", set())
        if members and set(members) <= published:
            return sorted(members)[0]
    raise AssertionError(
        f"{OWN_CONFIG} states no subset of a closed list the surface publishes, so this "
        "exemption asserts nothing"
    )


def _plant_an_inline_list_member(tree: Tree) -> Tree:
    """A value a configuration states as one member of an inline list.

    ⛔ The member is read out of whatever configuration supplies one rather than
    written here, so a project that reworks its list keeps the plant. Found when
    § 14's `inherits` became the first list of bare names a project writes: read
    the bracket as one string and no carrier could ever contain the value, which
    is a check reporting green while holding nothing for the key.
    """
    members = sorted(
        value for value, where in tree.forbidden_values().items() if where.endswith("inherits)")
    )
    if not members:
        raise AssertionError(
            "no configuration supplies an inline-list value, so this plant tests nothing"
        )
    return _plant_in_a_carrier(f"\nThe role reads `{members[0]}` from the shell.\n")(tree)


def _plant_foreign_slug_as_url(tree: Tree) -> Tree:
    tree.text["README.md"] += "\nSee <https://github.com/planted-owner/planted-repo>.\n"
    return tree


def _plant_cited_slug_outside_its_roots(tree: Tree) -> Tree:
    """A cited artifact's slug, permitted in `docs/`, planted in a carrier root.

    The table's whole point is that a citation is permitted *somewhere*; a
    permitted-everywhere entry would let a foreign slug through under cover of
    one, which is measurably what the first version of the entry did.
    """
    slug = next(iter(CITED_ARTIFACTS))
    target = next(
        (p for p in tree.strict() if p.endswith(".md")),
        "plugins/mjolnir/skills/planted/SKILL.md",
    )
    tree.text[target] = tree.text.get(target, "") + f"\nSee <https://github.com/{slug}>.\n"
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


def _plant_machine_address(tree: Tree) -> Tree:
    tree.text["README.md"] += "\nThe box answers on 203.0.113.7.\n"
    return tree


def _plant_jira_key_as_a_value(tree: Tree) -> Tree:
    tree.text["docs/configuration-surface.md"] += "\nMeasured on `PROJ-1421`.\n"
    return tree


def _plant_trello_id_as_a_value(tree: Tree) -> Tree:
    tree.text["docs/configuration-surface.md"] += "\nThe board is `5f2b1c9e4a7d8e3f0b6a1c2d`.\n"
    return tree


def _plant_account_id_as_a_value(tree: Tree) -> Tree:
    tree.text["docs/configuration-surface.md"] += (
        "\nThe account is `712020:11abcdef-2222-3333-4444-5566778899aa`.\n"
    )
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
    """Every scalar replaced by a placeholder: a sweep with nothing to look for.

    ⛔ Derived rather than written out, and it has to be: the reading is of every
    leaf, so a plant that blanked a list of named keys would leave the rest of the
    document stating values and assert nothing.
    """
    def blanked(node):
        if isinstance(node, dict):
            return {key: blanked(value) for key, value in node.items()}
        if isinstance(node, list):
            return [blanked(item) for item in node]
        return "<placeholder>"

    for path in tree.configs():
        tree.text[path] = yaml.safe_dump(blanked(yaml.safe_load(tree.text.get(path, "")) or {}))
    return tree


def _plant_an_unreadable_configuration(tree: Tree) -> Tree:
    """A configuration that does not parse must not read as one stating no values.

    The direction that matters: an unreadable file yields no values, which looks
    exactly like a file whose values are all placeholders and nothing like an
    error -- so the sweep would go quiet over a whole configuration and stay
    green.
    """
    tree.text[OWN_CONFIG] = tree.text.get(OWN_CONFIG, "") + "\nunreadable: [this, is\n"
    return tree


def _plant_a_surface_publishing_nothing(tree: Tree) -> Tree:
    """A surface with no alternation left in it.

    ⛔ What this asserts is that the published vocabulary is read **from the
    surface**: a sweep carrying its own copy of the alternations would not notice
    this plant at all. ⚠️ The failure direction here is a flood rather than a
    hole, which is why the arm reports the unreadable surface by name instead of
    letting a hundred false reds stand in for the explanation.
    """
    tree.text[SURFACE] = re.sub(r"\s*\|\s*", " ", tree.text.get(SURFACE, ""))
    return tree


VIOLATIONS = [
    ("no other repository is named", "a foreign slug in a URL", _plant_foreign_slug_as_url),
    ("no other repository is named", "a foreign slug in the install command", _plant_foreign_slug_in_install_command),
    ("no other repository is named", "a foreign slug as a config value", _plant_foreign_slug_as_config_value),
    ("no other repository is named", "a cited artifact's slug outside the roots its entry names", _plant_cited_slug_outside_its_roots),
    ("no other repository is named", "this project's own slug unstated", _plant_own_slug_unstated),
    ("no home directory is named", "an absolute home path", _plant_home_path),
    ("no home directory is named", "a tilde path", _plant_tilde_path),
    ("no home directory is named", "a home path in the sibling script", _plant_home_path_in_the_sibling_script),
    ("no address is named", "an email address", _plant_address),
    ("no machine is named", "a machine named by its address", _plant_machine_address),
    ("no tracker identifier is named", "a Jira key written as a value", _plant_jira_key_as_a_value),
    ("no tracker identifier is named", "a Trello object id written as a value", _plant_trello_id_as_a_value),
    ("no tracker identifier is named", "a tracker account id written as a value",
     _plant_account_id_as_a_value),
    ("no tracker identifier is named", "a Jira site", _plant_jira_site),
    ("no tracker identifier is named", "a Trello card URL", _plant_trello_url),
    ("the strict set is swept at all", "a strict set with no files in it", _plant_empty_strict_set),
    ("no carrier escapes the strict set", "a carrier in a root no shape reaches", _plant_carrier_in_an_unreachable_root),
    ("no tracker is named in the strict set", "a tracker named in a carrier",
     _plant_in_a_carrier("\nOn Trello the card moves separately.\n")),
    ("no tracker is named in the strict set", "a tracker named in its de-slugged spelling",
     _plant_in_a_carrier("\nOn GitHub Projects the item moves separately.\n")),
    ("no tracker is named in the strict set", "a surface declaring no tracker kinds", _plant_surface_with_no_tracker_kinds),
    ("no tracker is named in the strict set", "a tracker inside a hyphenated compound",
     _plant_in_a_carrier("\n  trello-sync:    { class: guard }\n")),
    ("no tracker is named in the strict set", "a tracker inside an underscored compound",
     _plant_in_a_carrier("\n  jira_sync:      { class: guard }\n")),
    ("no stack is named in the strict set", "a build tool invocation in a carrier",
     _plant_in_a_carrier("\nRun `npm run build` first.\n")),
    ("no stack is named in the strict set", "a build tool inside a hyphenated compound",
     _plant_in_a_carrier("\nRun `gradle-capacity --check` first.\n")),
    ("no stack is named in the strict set", "a build tool in a carrier entry's value",
     _plant_in_a_carrier("\nThe entry is `something: { class: guard, partial: \"npm only\" }`.\n")),
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
    # One per group of the flag list, which is the arm that was missing while a
    # flag was caught only where its command was. ⛔ Written alone, with no command
    # in front of it, because that is the shape nothing reddened on.
    ("no stack is named in the strict set", "a build tool's own flag written alone",
     _plant_in_a_carrier("\nRun it with `--no-daemon` so the verdict is this tree's.\n")),
    ("no stack is named in the strict set", "a flag that makes a command repair what it judges",
     _plant_in_a_carrier("\nPass `--fix` and read the diff afterwards.\n")),
    # The interpreter class, in the position the surface forbids: in front of
    # something configuration supplies, where the language is a guess.
    ("no stack is named in the strict set", "an interpreter prefixing a configured path",
     _plant_in_a_carrier("\nRun `python3 <ordering.command>` from the skills root.\n")),
    ("no stack is named in the strict set", "an interpreter prefixing a path nothing here holds",
     _plant_in_a_carrier("\nRun `node ./tooling/report.js` before the review.\n")),
    # ⚠️ A key's placeholder prefixed with an interpreter, which is the form the
    # rule above permits nowhere: a configured path is a guess about the language
    # the script behind it happens to be in, whichever key names it.
    ("no stack is named in the strict set",
     "an interpreter prefixing a key's placeholder rather than a command stated whole",
     _plant_in_a_carrier("\nRun `python3 <day_log.script> --check` here too.\n")),
    # The same construct against rule 1's reader: `code()` pairs spans per line,
    # so a double span ahead of a command is where that pairing goes wrong.
    ("no stack is named in the strict set", "a build tool after a double span",
     _plant_in_a_carrier("\nMatching `` `x` is retired `` and then `npm run build` first.\n")),
    ("no value is carried in the strict set", "a status word in a carrier",
     _plant_in_a_carrier("\nMove the item to `In Progress` first.\n")),
    ("no value is carried in the strict set", "a status word whose wrap falls inside it",
     _plant_in_a_carrier("\nMove the item to `In\nProgress` first.\n")),
    ("no value is carried in the strict set", "an upper-case status word",
     lambda tree: _plant_in_a_carrier("\nMove the item to `IN_PROGRESS` first.\n")(
         _plant_upper_case_status(tree))),
    ("no value is carried in the strict set", "a single-quoted value in a hook",
     lambda tree: _plant_in_a_hook("status='In Progress'\n")(tree)),
    ("no value is carried in the strict set", "a member of an inline list value",
     _plant_an_inline_list_member),
    # ⛔ One per arm of the ``…`` handling, because each fails differently and
    # the two plants above reach that handling only through prose some document
    # happens to carry. The measured incident was the third of these.
    ("no value is carried in the strict set", "a status word inside a double span",
     _plant_in_a_carrier("\nWrite it as `` `In Progress` `` in the body.\n")),
    ("no value is carried in the strict set", "a status word after an unclosed double span",
     _plant_in_a_carrier("\nA span `` opened and never closed, then `In Progress`.\n")),
    ("no value is carried in the strict set", "a status word between two double spans",
     _plant_in_a_carrier("\n`` A `` then `In Progress` then `` B ``.\n")),
    # ⛔ One per shape a list of key names cannot reach, each reading its value
    # out of the configuration rather than carrying it.
    ("no value is carried in the strict set", "a configured branch prefix, under a key the project names",
     _plant_a_configured_branch_prefix),
    ("no value is carried in the strict set", "a configured label, under a plural whose singular means something else",
     _plant_a_configured_label),
    ("no value is carried in the strict set", "a configured value as a JSON value",
     lambda tree: _plant_in_a_json_carrier(
         '{"statusMessage": "%s"}\n' % _a_configured(tree, "tracker", "labels"))(tree)),
    # ⛔ One per fact § 2's facet holds, because each is a separate thing a
    # carrier could copy and the three have separate homes in an entry. The
    # outcome they assert is #47's: every consumer of the host's checks reads
    # `host.checks`, and none carries a workflow name, a trigger pattern or a
    # path filter of its own -- which is a property of the *search* rather than
    # of whoever read the skills last.
    ("no value is carried in the strict set", "a workflow name, the key the facet is read by",
     lambda tree: _plant_in_a_carrier(
         f"\nWait for the `{_a_facet_value(tree, 'workflow')}` run.\n")(tree)),
    ("no value is carried in the strict set", "a trigger pattern out of the facet",
     lambda tree: _plant_in_a_carrier(
         f"\nThe run starts on `{_a_facet_value(tree, 'triggers')}`.\n")(tree)),
    ("no value is carried in the strict set", "a path filter out of the facet",
     _plant_a_configured_path_filter),
    # The three ways this check can hold nothing and report green.
    ("no value is carried in the strict set", "a surface that publishes nothing",
     _plant_a_surface_publishing_nothing),
    ("no value is carried in the strict set", "a configuration that does not parse",
     _plant_an_unreadable_configuration),
    ("no value is carried in the strict set", "configurations with no concrete value left", _plant_configurations_with_no_concrete_value),
    # One per spelling of asking who is running, because each is a different
    # surface a role could reach for -- the host's own flag value, a tracker
    # query, and the shell -- and the list is closed, so a spelling with no plant
    # is a spelling nothing asserts is read at all.
    ("no role is resolved through the running user",
     "the code host's current-user spelling in a carrier",
     _plant_in_a_carrier("\nAssign it with `--add-assignee @me` once the branch is cut.\n")),
    ("no role is resolved through the running user",
     "a tracker query for the current user, written in prose",
     _plant_in_a_carrier("\nCompare the assignee against currentUser rather than a map.\n")),
    # ⛔ The flag, which the first form of this grammar let through: the dash in
    # front of it was rejected by a lookbehind written for the word.
    ("no role is resolved through the running user",
     "a flag naming the current user",
     _plant_in_a_carrier("\nRun it with `--current-user` to see the other reading.\n")),
    ("no role is resolved through the running user",
     "the shell asked who is running",
     _plant_in_a_hook("# Resolve the reviewer.\nreviewer=$(whoami)\n")),
]


# Assertions in the other direction: a plant each check must *not* redden on.
# A check whose scope is wider than it was written for is as broken as one that
# cannot fail, and the only thing that catches a scope widening is asserting the
# green side of it. Each entry names the exemption it holds, so tightening one
# makes a named assertion fail rather than silently sweeping more of the tree.
EXEMPTIONS: list[tuple[str, str, object]] = [
    ("no value is carried in the strict set", "a status word in a script a carrier calls",
     _plant_in_a_carrier_implementation("STATES = ('open', 'closed')\n")),
    ("no stack is named in the strict set", "a build tool a script a carrier calls invokes",
     _plant_in_a_carrier_implementation('subprocess.run(["npm", "run", "build"])\n')),
    # The narrowest exception, asserted in the direction that matters: a carrier
    # map's KEY may name a build tool, because the key is the name a project
    # actually gave that carrier. ⚠️ Verified by disabling `carrier_name_exception`
    # and watching this plant redden -- an exemption nothing can fail is an
    # exemption nobody checked.
    ("no stack is named in the strict set", "a build tool in a carrier map's key",
     _plant_in_a_carrier("\nThe entry is `gradle-capacity: { class: guard }`.\n")),
    # ⛔ The green side of the line this check draws, one plant per shape the
    # surface publishes a vocabulary in. A sweep that forbade either would forbid
    # a role from naming the section that routes it: § 6's dirty-tree derivation
    # and § 10's routing table are both stated *by mode*. ⚠️ Verified by emptying
    # the published set and watching both redden -- an exemption nothing can fail
    # is an exemption nobody checked.
    ("no value is carried in the strict set", "a value the surface publishes as an alternation",
     lambda tree: _plant_in_a_carrier(
         f"\nThe model is `{_a_published_alternation_member(tree)}`.\n")(tree)),
    ("no value is carried in the strict set", "a member of a closed list the surface publishes",
     lambda tree: _plant_in_a_carrier(
         f"\nThe stream is `{_a_published_list_member(tree)}`.\n")(tree)),
    # And the narrowest of the four exceptions one format over: in JSON a key is
    # quoted by construction, so rule 2 reads every key of a hook carrier as a
    # value. The value beside it is swept, which is a planted violation above.
    ("no value is carried in the strict set", "a configured value as a JSON object key",
     lambda tree: _plant_in_a_json_carrier(
         '{"%s": {"type": "command"}}\n' % _a_configured(tree, "tracker", "labels"))(tree)),
    # ⛔ One per position the interpreter arm lets through, because each is a
    # different reason and a sweep widened past any of them reddens a shipped
    # carrier. ⚠️ Verified by disabling each arm in turn and watching its own
    # plant redden -- an exemption nothing can fail is an exemption nobody checked.
    ("no stack is named in the strict set", "an interpreter in front of a path the plugin ships",
     _plant_in_a_carrier(
         '\nRun `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/config.py"` first.\n')),
    ("no stack is named in the strict set",
     "an interpreter in front of a file this repository tracks",
     lambda tree: _plant_in_a_carrier(
         f"\nRun `python3 {_a_tracked_script(tree)}` from the root.\n")(tree)),
    # The shape a hook carrier is in: the interpreter is the whole value of its
    # own key, and what it runs is a separate member of the object.
    ("no stack is named in the strict set", "an interpreter with nothing after it",
     _plant_in_a_json_carrier(
         '{\n  "command": "python3",\n  "args": ["a-path-of-its-own"]\n}\n')),
    # ⚠️ The day-log role's own invocation, planted inside that role's own
    # directory so the green side of this scope is asserted where the live text
    # relying on it sits rather than only in general. It is the one role that runs
    # a script of the plugin's rather than a command a project states.
    ("no stack is named in the strict set",
     "the day-log role naming the script the plugin ships",
     _plant_in_a_named_root(
         ["plugins/mjolnir/skills/day-report/"],
         '\nRun `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/day_log.py" --month YYYY-MM`.\n')),
    # ⛔ The green side of § 27's own distinction, and the one that makes the check
    # above the rule rather than a wider ban: an implementation behind `assign`
    # translates the running user's spelling, because recording who *took* an item
    # is a fact about this run. ⚠️ Verified by widening the sweep from the strict
    # set to the whole tree and watching this plant redden -- an exemption nothing
    # can fail is an exemption nobody checked.
    ("no role is resolved through the running user",
     "the host's own spelling in a script a carrier calls",
     _plant_in_a_carrier_implementation('def assign(who: str = "@me"): ...\n')),
    # ⛔ The hyphenated English modifier, which is the phrase a carrier
    # describing this rule reaches for and is not a spelling that resolves
    # anybody. ⚠️ Verified by separating the two words on `[_-]?` again and
    # watching this plant redden — which is how the false refusal was found,
    # inside a change whose own subject is this rule.
    ("no role is resolved through the running user",
     "the hyphenated English modifier in a carrier's prose",
     _plant_in_a_carrier(
         "\nThe host's current-user spelling is what § 27 forbids a role reaching for.\n")),
    # ⛔ The green side of the account-id grammar, and the reason it is the
    # prefixed spelling alone: a bare dashed hex group is a *session* id in this
    # repository's own fixtures, which is nobody. ⚠️ Verified by making the prefix
    # optional again and watching this plant redden -- which is how the false red
    # was found rather than reasoned about.
    ("no tracker identifier is named", "a session id, which is a dashed hex group and nobody",
     lambda tree: _plant_in_a_carrier_implementation(
         'SESSION = "aaaabbbb-0000-0000-0000-000000000000"\n')(tree)),
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
    for name, label, plant in EXEMPTIONS:
        if by_name[name](plant(tree.copy())):
            print(f"  REDDENED ON EXEMPTION  {name}: {label}")
            failures += 1
        else:
            print(f"  green on exemption     {name}: {label}")
    if failures:
        print(f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a check, "
              "and one that reddens past its scope is not this check.")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a != "--self-test"]
    if unknown:
        print(f"unrecognised argument(s): {' '.join(unknown)}\n\n{__doc__}")
        return 2

    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    tree = Tree(root)

    if "--self-test" in argv:
        print(f"Asserting each check reddens on its planted violations ({len(VIOLATIONS)}) "
              f"and stays green on its exemptions ({len(EXEMPTIONS)}):")
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
