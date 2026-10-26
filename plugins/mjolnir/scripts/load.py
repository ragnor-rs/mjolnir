#!/usr/bin/env python3
"""The restoring role's readings, and the evidence each one is read out of.

The counterpart of the bookkeeping role one module over: that one **persists**
what happened at a boundary, this one **restores** what is in flight at the start
of a pass. `../config/schema.md` § 24 states what the role is, which readings it
takes and the two rules it inherits; ⛔ **this module states none of that** and
owns what neither the role nor a later pass should perform twice:

  * **The readings**, in the procedure's order, each with what it reads and
    whether that mechanism is there at all -- the shape `save.py` has for the
    thirds, and for the same reason: a reading that silently did not happen reads
    exactly like one that found nothing (§ 11).
  * **Where the work is**, read out of git in one place: the branch, its upstream,
    its position against the base and against its own published ref, what is
    committed and not pushed, and what is in the tree and not committed.
  * **What the last pass was doing**, read out of the harness's own session store
    -- which transcripts belong to this working directory, what each one's last
    instruction and last reply were, and every compaction boundary in it with
    what that compaction dropped.
  * **Whether a working file that is gone can be replayed**, answered from the
    calls the transcript records rather than from a hope that it can.
  * **The window's own reading**, where the harness hands one to a `SessionStart`
    arm.

⛔ **Every subcommand is read-only, and that is asserted rather than asserted
about.** The suite runs each of them against a tree where a naive implementation
would have written -- a store that does not exist, a working file that is missing
-- and holds the tree to being byte-identical afterwards. ⚠️ **The one exception
is named rather than smoothed over**: reading a working tree's state through git
may refresh git's own index, which is git's cache and not this module's output, so
the assertion is that no file is created or removed anywhere and that nothing but
that index differs.

⛔ **Nothing here fetches**, which is § 24's read-only half arriving in one
place: every answer about a remote is read against the remote-tracking refs the
tree already has, and each one says so in its own output. ⚠️ **One reading may
still ask the remote** -- where a clone recorded no default branch, the base's
name is derived by querying it, which writes nothing and is avoidable by naming
the base on the invocation. The rule is § 24's; what is local to this module is
that the asking is reported rather than hidden.

⚠️ **What a compaction leaves behind is measured rather than assumed**, because
the replay answer below rests on it: a compaction **appends** two records to the
same transcript file -- a `system` record carrying `compactMetadata` and a `user`
record flagged `isCompactSummary` -- and every record before the boundary stays in
the file. The figures behind that are in `docs/configuration-surface.md`.

Usage:
    load.py [--skills-root DIR]        the readings this project's load takes
    load.py where --repo-root DIR      where the work is, read-only and unfetched
                [--remote NAME] [--base BRANCH]
    load.py session --root DIR         what the last pass was doing, from the store
                [--store DIR] [--exclude NAME]
    load.py replay --missing PATH      whether a file that is gone replays, and
                --transcript PATH      from what
    load.py resume                     the `SessionStart` arm, payload on stdin

⚠️ **`--base` and `--exclude` are the two flags a role is expected to pass** and
the reason each exists is a reading that is wrong without it: an underived base
is a position against nothing, and an unexcluded transcript is the file this pass
is writing read back as the pass before it.

Exit status, and ⛔ **four values rather than two**: 0 the reading was produced,
1 nothing is being asked about -- a path that is not a repository, a store that
is not there, a transcript that is not one -- 2 something that had to be read
could not be, which is a configuration that does not resolve and a store whose
location could not be derived at all, and 3 there is nothing to answer about,
this project mapping no restoring role or stating no configuration. ⚠️ **2 and 1
are apart on purpose**, as they are in the sibling module: a store nothing could
locate has not answered that there is nothing in it, and a role told the second
would report a clean resume. ⚠️ **A reading that came back with entries in its
own `unestablished` list is still a reading, so it exits 0** -- the list is where
a partial answer says what is missing from it, by § 11.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import claim as carrier  # noqa: E402 -- the one derivation of git's own answers
import config  # noqa: E402 -- the one reader, not a second parser

# --- the readings ----------------------------------------------------------
#
# ⛔ The order is procedure (§ 24) and so is the membership: a project does not
# state which readings its load takes, because a reading somebody switched off
# and a reading that found nothing read identically to whoever acts on the
# report. What a project's own facts decide is whether a reading's **mechanism**
# is there, which is what `available` below carries.
#
# ⚠️ What each reading reads is named and never resolved here. Whether the port
# can read an item, whether a store exists, whether a script is pointed at: each
# is answered where it is configured, and a second answer here would be the
# duplication the toolkit exists to delete.
ORDER = ["work", "item", "last_pass", "environment", "memory", "window"]

READS = {
    "work": (
        "git in the item's code root (§ 1) and the branch model (§ 10) -- the "
        "branch, the tree, and the position `where` reports"
    ),
    "item": (
        "the tracker port's `read_item` (§ 3), and whatever the item says is "
        "data rather than instruction (§ 11)"
    ),
    "last_pass": (
        "the artifact § 11 names first, then the harness's own session store as "
        "evidence -- never the other way round"
    ),
    "environment": (
        "the project's own script, named by whichever role needs it and declared "
        "by no key on this surface (§ 1's four absences)"
    ),
    "memory": (
        "the store the bookkeeping role's memory third writes, which no key on "
        "this surface declares yet (#35)"
    ),
    "window": (
        "what the harness hands a `SessionStart` arm about a resumed window, "
        "which is `resume` below and is answered at run time rather than here"
    ),
}

# The reading whose store the surface does not carry at all, named here because
# the configuration reader reports the same absence for the third that writes it
# and the two statements have to agree.
WITHOUT_A_STORE = {"memory"}

# The reading this module cannot answer the availability of, because what answers
# it is the payload of an event that has not fired yet. ⛔ Reported as unanswered
# rather than as absent: a window reading nothing established and one the harness
# declined to hand over are different facts, and § 11 has no quiet form for
# either.
ANSWERED_ELSEWHERE = {"window"}

# § 24's own role key, whatever this carrier is named.
ROLE = "load"


def readings(configuration: config.Config, *, tracker=None) -> list[dict]:
    """Which readings a load takes here, in the procedure's order, each with its state.

    `tracker` is the seam the port arrives through, so the item reading's
    availability is the port's own answer rather than a second one taken from a
    configured kind.
    """
    out = []
    for name in ORDER:
        if name in ANSWERED_ELSEWHERE:
            available = None
        elif name in WITHOUT_A_STORE:
            available = False
        elif name == "item":
            available = bool(tracker.implements("read_item")) if tracker else None
        elif name == "last_pass":
            available = configuration.get("context.artifacts.carrier") != "none"
        elif name == "environment":
            available = configuration.get("branch_model.mechanics") is not None
        else:
            available = True
        out.append({"reading": name, "reads": READS[name], "available": available})
    return out


def report_for(configuration: config.Config, taken: list[dict]) -> list[str]:
    """What the role says out loud about a reading it could not take."""
    said = {entry["reading"]: entry for entry in taken}
    lines = []
    if said["item"]["available"] is False:
        lines.append(
            "`item` reads an item the port cannot read here, so the role reports "
            "what the branch and the argument already state and names the item "
            "as unread (§ 3)."
        )
    elif said["item"]["available"] is None:
        lines.append(
            "`item` could not be asked about, the port not having been reached: "
            "the role reports it unanswered rather than as an item with nothing "
            "to say (§ 11)."
        )
    if not said["last_pass"]["available"]:
        lines.append(
            "No artifact store is carried (`context.artifacts.carrier: none`), so "
            "there is no handoff to read first and `last_pass` falls to the "
            "session store alone -- which is evidence and not a handoff (§ 11)."
        )
    if not said["environment"]["available"]:
        lines.append(
            "`branch_model.mechanics` is null, so this project points at no setup "
            "of its own and the role reports the environment as a reading it could "
            "not take. ⛔ Not that the environment is up: the surface carries no "
            "key for one and names it a project's own script (§ 1)."
        )
    else:
        # ⛔ The pointer's own value, because the reading is taken by running what
        # it names: a report saying only that the project points at something left
        # the role with nothing to run and no key it was allowed to read it from.
        # Found by review on this change.
        lines.append(
            f"`branch_model.mechanics` points at "
            f"`{configuration.get('branch_model.mechanics')}`, which is the project's "
            "own setup and teardown: the environment reading is taken by reading what "
            "it names, and ⛔ never by running a teardown (§ 10)."
        )
    if not said["memory"]["available"]:
        lines.append(
            "`memory` reads a store no key on this surface declares (#35), so the "
            "role says what it could not check rather than restating a recalled "
            "fact as current (§ 24)."
        )
    if said["window"]["available"] is None:
        lines.append(
            "`window` is answered by the `resume` arm out of a payload this "
            "command never sees, so what it carries is read where it arrives and "
            "reported as unhanded where the harness states nothing (§ 24)."
        )
    if configuration.get("branch_model.kind") == "worktree":
        lines.append(
            "The branch model cuts a tree per item, so the session store holds a "
            "directory per tree as well as one for the checkout: `session` is run "
            "for the tree the work is in **and** for the checkout it was cut "
            "from, or the earlier passes on this item are missed (§ 10)."
        )
    return lines


# --- where the work is -----------------------------------------------------
#
# ⛔ One place, because the position is four questions that are each cheap to
# answer and expensive to answer differently: a role asking git by hand asks some
# of them, and the two that bite -- a commit that was never pushed, and a branch
# behind the ref it is published on -- are the two that read as *nothing to do*.

# What a position is read against where the remote names itself nothing else.
REMOTE = "origin"

# How long the one network-touching derivation may take before the position is
# reported with the base unestablished. ⚠️ A bound rather than none, which is
# this module's own departure from the carrier's default: a sweep is the first
# thing a pass runs, so a reading that hangs is a pass that never starts.
BASE_TIMEOUT = 10.0

# How many unpushed commits are named before the rest are counted. ⚠️ The limit
# is here rather than in the role's text so that the answer is the same for every
# reader of it, and the count is always stated: a list silently cut to its head
# reads as the whole of what is unpushed.
NAMED_COMMITS = 20


def _counts(root: str | Path, left: str, right: str = "HEAD") -> tuple[int, int] | None:
    """(commits in `left` not in `right`, commits in `right` not in `left`)."""
    proc = carrier.git(
        root, "rev-list", "--left-right", "--count", f"{left}...{right}", check=False
    )
    if proc.returncode != 0:
        return None
    parts = proc.stdout.split()
    if len(parts) != 2:
        return None
    try:
        return int(parts[0]), int(parts[1])
    except ValueError:
        return None


def _ref_exists(root: str | Path, ref: str) -> bool:
    return carrier.git(root, "rev-parse", "--verify", "--quiet", ref, check=False).returncode == 0


def position(root: str | Path, *, remote: str = REMOTE, base: str | None = None) -> dict:
    """Where the work is, read-only and without fetching.

    ⛔ Every answer that depends on the remote is stated as being against the
    remote-tracking refs this tree already has, and the command that refreshes
    them is named rather than run.
    """
    answer: dict = {
        "root": str(root),
        "as_of": (
            "the remote-tracking refs as this tree last fetched them; nothing here "
            f"fetched. `git -C {root} fetch {remote}` is what refreshes them, and it "
            "writes, so it is a person's call rather than this sweep's. ⚠️ One reading "
            "here may still **ask** the remote: where this clone recorded no default "
            "branch, the base's name is derived by querying it — a read that writes "
            "nothing, bounded, and avoidable by naming the base on the invocation"
        ),
        "unestablished": [],
    }
    # ⛔ Whether this is a repository at all, asked before anything is read out of
    # it: `rev-parse HEAD` fails on a repository whose branch has no commit yet,
    # and the one arm below reported that as not a repository — a flatly false
    # reading of a freshly created project. Found by review on this change.
    if carrier.git(root, "rev-parse", "--git-dir", check=False).returncode != 0:
        answer["unestablished"].append(
            "this is not a git repository, or git could not read it"
        )
        return answer
    head = carrier.git(root, "rev-parse", "--abbrev-ref", "HEAD", check=False)
    if head.returncode != 0:
        named = carrier.git(root, "symbolic-ref", "--short", "HEAD", check=False)
        answer["branch"] = named.stdout.strip() or None
        answer["unestablished"].append(
            "this repository has no commit on its checked-out branch, so there is no "
            "position to read: the branch exists and nothing is on it"
        )
        return answer
    branch = head.stdout.strip()
    answer["branch"] = branch
    answer["detached"] = branch == "HEAD"
    answer["item_in_branch"] = carrier.item_in_branch(branch) if branch else None

    upstream = carrier.git(
        root, "rev-parse", "--abbrev-ref", "--symbolic-full-name", "@{upstream}", check=False
    )
    answer["upstream"] = upstream.stdout.strip() if upstream.returncode == 0 else None

    # The base, derived rather than named -- the one derivation of it there is.
    if base is None:
        try:
            base = carrier.integration_branch(root, remote, timeout=BASE_TIMEOUT)
        except Exception as exc:  # the carrier names what it could not derive
            answer["unestablished"].append(f"the base branch could not be derived: {exc}")
            base = None
    answer["base"] = base

    # ⛔ The hazard § 10 names: a branch cut without tracking disabled tracks the
    # **base**, and then a bare push writes to the base. Reported here because a
    # sweep is where it is cheap to see and a push is where it is not.
    answer["upstream_is_base"] = bool(
        answer["upstream"] and base and answer["upstream"] in (base, f"{remote}/{base}")
    )

    published = f"{remote}/{branch}" if branch and not answer["detached"] else None
    answer["published_ref"] = published if published and _ref_exists(root, published) else None
    if published and not answer["published_ref"]:
        answer["unpushed_branch"] = True
    else:
        answer["unpushed_branch"] = False

    # Against the branch's own published ref: what is committed here and is not
    # there, and what is there and is not here.
    if answer["published_ref"]:
        counted = _counts(root, answer["published_ref"])
        if counted is None:
            answer["unestablished"].append(
                f"the position against `{answer['published_ref']}` could not be counted"
            )
        else:
            behind, ahead = counted
            answer["behind_published"] = behind
            answer["ahead_of_published"] = ahead

    # Against the base, which is the other direction a branch goes stale in.
    # ⛔ Not where the derived base **is** this branch, which is what the one
    # derivation of it falls back to in a repository with no remote: counting a
    # branch against itself prints a confident pair of zeroes for a reading
    # nobody took. Found by review on this change.
    if base and base == branch:
        answer["unestablished"].append(
            f"the base derived to `{base}`, which is this branch: with no remote "
            "recording a default there is nothing to compare against, so the position "
            "against the base is unread rather than zero. Name the base on the "
            "invocation"
        )
    elif base:
        for ref in (f"{remote}/{base}", base):
            if not _ref_exists(root, ref):
                continue
            counted = _counts(root, ref)
            if counted is None:
                # ⛔ Inside the loop rather than after it: a ref that exists and
                # cannot be counted left the local candidate unread, because the
                # `break` sat outside this arm. Found by review on this change.
                continue
            answer["base_ref"] = ref
            answer["behind_base"], answer["ahead_of_base"] = counted
            break
        if "base_ref" not in answer:
            answer["unestablished"].append(
                f"neither `{remote}/{base}` nor `{base}` is a ref this tree has that "
                "could be counted, so the position against the base is unread"
            )

    # What is committed and not published. ⛔ Named, not counted alone: a count
    # says a push is owed and the subjects say what would go out with it.
    # ⚠️ Where the branch has no ref of its own, the span is every commit this
    # head reaches that no remote-tracking ref does -- which is the same question
    # asked of a branch that was never pushed, rather than a different one.
    span = (
        [f"{answer['published_ref']}..HEAD"]
        if answer["published_ref"]
        else ["HEAD", "--not", "--remotes"]
    )
    log = carrier.git(root, "log", "--format=%h %s", *span, check=False)
    if log.returncode == 0:
        lines = [line for line in log.stdout.splitlines() if line.strip()]
        answer["unpushed_count"] = len(lines)
        answer["unpushed"] = lines[:NAMED_COMMITS]
        answer["unpushed_unnamed"] = max(0, len(lines) - NAMED_COMMITS)
    else:
        answer["unestablished"].append("the unpushed commits could not be read")

    # ⛔ `--untracked-files=all` and not the default: a directory of untracked
    # files is one line under the default, which is the shape that let a tree
    # read as nearly clean one role over.
    dirty = carrier.git(root, "status", "--porcelain", "--untracked-files=all", check=False)
    if dirty.returncode == 0:
        entries = [line for line in dirty.stdout.splitlines() if line.strip()]
        answer["dirty_count"] = len(entries)
        answer["dirty"] = entries[:NAMED_COMMITS]
        answer["dirty_unnamed"] = max(0, len(entries) - NAMED_COMMITS)
    else:
        answer["unestablished"].append("the tree's own state could not be read")

    answer["report"] = _position_report(answer)
    return answer


def _position_report(found: dict) -> list[str]:
    """The two readings that look like *nothing to do*, said out loud."""
    lines = []
    if found.get("detached"):
        # ⛔ Said rather than left to be read off a `branch` of `HEAD`: a detached
        # tree carries no claim and no item, so every other line here is about a
        # position nothing owns. Found by review on this change.
        lines.append(
            "The tree is on no branch at all, so nothing here claims a work item and "
            "the readings below are about a detached head (§ 10)."
        )
    if found.get("unpushed_count"):
        lines.append(
            f"{found['unpushed_count']} commit(s) are committed here and are not on "
            f"{found.get('published_ref') or 'any remote'}: work that is done and that "
            "nothing outside this tree has."
        )
    if found.get("behind_published"):
        lines.append(
            f"The branch is {found['behind_published']} commit(s) behind "
            f"{found['published_ref']} as last fetched, so something outside this tree "
            "moved the claim's own ref."
        )
    if found.get("unpushed_branch"):
        lines.append(
            "The branch has no ref on the remote at all, so nothing outside this tree "
            "holds the claim or the work."
        )
    if found.get("upstream_is_base"):
        lines.append(
            f"The upstream is `{found['upstream']}`, which is the base: a bare push from "
            "here writes to the base (§ 10). Clear it before pushing."
        )
    if found.get("behind_base"):
        lines.append(
            f"The branch is {found['behind_base']} commit(s) behind `{found['base_ref']}` "
            "as last fetched."
        )
    if found.get("dirty_count"):
        lines.append(
            f"{found['dirty_count']} path(s) are in the tree and not committed. ⛔ Nothing "
            "was stashed, moved or committed here (§ 24)."
        )
    return lines


# --- what the last pass was doing ------------------------------------------
#
# ⚠️ The store and the slug are the **harness's** conventions, measured rather
# than published: one directory per working directory, named by replacing every
# character outside `[A-Za-z0-9-]` in its real path with `-`, and one transcript
# file per session inside it. ⛔ So a derived directory that is not there is
# reported as not found rather than as a project with no history -- the
# convention is free to change, and the direction that fails safe is saying so.

# ⛔ **No path on anybody's machine is written here.** The store sits under the
# harness's own configuration directory, which is read out of the environment
# rather than spelled out: `CLAUDE_CONFIG_DIR` where the shell holds it -- the
# harness's own relocation of that directory -- and the home directory the
# project states it hands a role (§ 14) otherwise. ⚠️ What stays a literal is the
# harness's own two directory names, which are a convention like the slug rule
# below rather than a value belonging to a machine.
CONFIG_DIR = "CLAUDE_CONFIG_DIR"
HOME = "HOME"
HARNESS_DIR = ".claude"
SESSIONS_UNDER = "projects"
BACKUPS_UNDER = "file-history"


def harness_dir() -> Path | None:
    """The harness's own configuration directory, or None where neither name resolves."""
    stated = os.environ.get(CONFIG_DIR)
    if isinstance(stated, str) and stated.strip():
        return Path(stated.strip())
    home = os.environ.get(HOME)
    if isinstance(home, str) and home.strip():
        return Path(home.strip()) / HARNESS_DIR
    return None


# The record a compaction leaves, and the one that carries the summary it was
# replaced by. Both are the harness's own field names.
BOUNDARY_TYPE = "compact_boundary"
SUMMARY_FLAG = "isCompactSummary"

# The records a lost file can be replayed out of, and the field each names a path
# in. ⛔ Only a full write can start a replay: an edit states a difference, so a
# chain that opens with one is a chain against content this file never saw.
WRITING_CALLS = {
    "Write": ("file_path", True),
    "Edit": ("file_path", False),
    "MultiEdit": ("file_path", False),
    "NotebookEdit": ("notebook_path", False),
}

# How much of an instruction or a reply is quoted back. ⚠️ A bound rather than
# the whole text: the point of the reading is what the last pass was doing, and a
# sweep that pastes two full turns into the window has spent the resource § 11
# makes this role's subject.
QUOTED = 400

# How many of a store's transcripts are read back. ⛔ A bound rather than none,
# and the reason is this module's own subject: the store this sweep reads holds
# every session that ever ran in a working directory, and reading all of them
# spends the window § 11 makes this role's business. What is beyond the bound is
# counted and named rather than dropped in silence.
READ_BACK = 3

def history_root() -> Path | None:
    """Where the harness keeps the copy a file had **before** an edit.

    Named rather than read: it is the second place a lost file may be, and a
    sweep that says *not replayable* without naming it has under-reported.
    """
    found = harness_dir()
    return found / BACKUPS_UNDER if found else None


def store_dir_for(root: str | Path, store: str | Path | None = None) -> Path | None:
    """The harness's own store directory for this working directory."""
    if store:
        under = Path(store)
    else:
        found = harness_dir()
        if found is None:
            return None
        under = found / SESSIONS_UNDER
    real = os.path.realpath(str(root))
    return under / re.sub(r"[^A-Za-z0-9-]", "-", real)


def _records(path: Path):
    """Every record of a transcript, with its line number, skipping what will not parse.

    ⚠️ A line that does not parse is skipped rather than fatal: a transcript is
    being appended to while this reads it, so the last line of a live one is
    legitimately half-written.

    ⛔ **Read as bytes and decoded per line**, which is not where this started: a
    half-written line is frequently half-written *inside a character*, and the
    decode then raised out of the iteration rather than out of the `json` call
    the skip was wrapped around — so a sweep over a live transcript died on the
    one case the comment above says it handles. Found by review on this change.
    """
    with path.open("rb") as handle:
        for number, raw in enumerate(handle, 1):
            try:
                line = raw.decode("utf-8").strip()
            except UnicodeDecodeError:
                continue
            if not line:
                continue
            try:
                yield number, json.loads(line)
            except ValueError:
                continue


# What the harness writes into a transcript as a `user` record that no person
# typed: the output and the caveats of a command the person ran, and the command
# itself. ⛔ **Matched on the harness's own markup because no field marks them**,
# measured: the caveat record carries `isMeta` and the other two carry nothing
# this reader can tell from a real turn. ⚠️ So the list is the weak half of this
# reading and is named as such — a marker the harness renames is a plumbing
# record read as an instruction again, and the direction that fails is the
# report, not the sweep.
PLUMBING = (
    "<local-command-stdout>",
    "<local-command-stderr>",
    "<local-command-caveat>",
    "<command-name>",
    "<command-message>",
    "<command-args>",
)
META = "isMeta"

# A span the harness appends to a real turn rather than a record of its own, so
# it is stripped from the text instead of disqualifying it.
REMINDER = re.compile(r"<system-reminder>.*?</system-reminder>", re.S)


def _text_of(record: dict) -> str:
    """The text a user or assistant record carries, flattened and without appended spans."""
    message = record.get("message") or {}
    content = message.get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        parts = [
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        text = "\n".join(part for part in parts if part)
    else:
        return ""
    return REMINDER.sub("", text).strip()


def _is_plumbing(record: dict, text: str) -> bool:
    """Whether this `user` record is the harness talking to itself.

    ⛔ The reason the arm exists: over this repository's own store, the last
    `user` record of most finished sessions is the output of the command that
    ended them, so a reading that took it reported *what the last pass was
    doing* as a farewell. Measured at 78 of 138 before this arm.
    """
    if record.get(META):
        return True
    stripped = text.lstrip()
    return any(stripped.startswith(tag) for tag in PLUMBING)


def _trim(text: str) -> str:
    flat = " ".join(text.split())
    if len(flat) <= QUOTED:
        return flat
    return flat[:QUOTED] + f" … (trimmed at {QUOTED} characters)"


def transcript(path: Path) -> dict:
    """One transcript's own evidence: what it ended on, and what it has lost."""
    found: dict = {
        "file": path.name,
        # ⛔ The whole path and not the name alone: `replay` below takes a
        # transcript by path, so a reading that printed the name left the role
        # joining it to the store itself. Found by review on this change.
        "path": str(path),
        "records": 0,
        "boundaries": [],
        "last_instruction": None,
        "last_reply": None,
        # ⛔ Which of the two the transcript **ends** on, rather than whether a
        # reply was ever written: a session with twenty finished turns that died
        # on the twenty-first carries a reply, and comparing the two last values
        # read it as finished. That is the whole tell this reading exists for, so
        # it is the record's own order that answers rather than two nulls.
        # Found by review on this change.
        "ended_on": None,
        "files_written": [],
    }
    seen_paths: list[str] = []
    for _number, record in _records(path):
        found["records"] += 1
        kind = record.get("type")
        if record.get("subtype") == BOUNDARY_TYPE:
            meta = record.get("compactMetadata") or {}
            found["boundaries"].append({
                "trigger": meta.get("trigger"),
                "before": meta.get("preTokens"),
                "after": meta.get("postTokens"),
                "dropped": meta.get("cumulativeDroppedTokens"),
            })
            continue
        if record.get(SUMMARY_FLAG):
            continue
        if kind == "user":
            text = _text_of(record)
            if text and not _is_plumbing(record, text):
                found["last_instruction"] = _trim(text)
                found["ended_on"] = "an instruction"
        elif kind == "assistant":
            text = _text_of(record)
            if text:
                found["last_reply"] = _trim(text)
                found["ended_on"] = "a reply"
        message = record.get("message") or {}
        content = message.get("content")
        if isinstance(content, list):
            for block in content:
                if not isinstance(block, dict) or block.get("type") != "tool_use":
                    continue
                named = WRITING_CALLS.get(str(block.get("name")))
                if not named:
                    continue
                field, _full = named
                where = (block.get("input") or {}).get(field)
                if isinstance(where, str) and where not in seen_paths:
                    seen_paths.append(where)
    found["files_written"] = seen_paths
    found["compacted"] = bool(found["boundaries"])
    return found


def session(root: str | Path, *, store: str | Path | None = None, exclude: str = "") -> dict:
    """What the last pass was doing, read out of the harness's own store."""
    where = store_dir_for(root, store)
    answer: dict = {
        "root": os.path.realpath(str(root)),
        "store": str(where) if where else None,
        "derivation": (
            "the harness's own convention, measured rather than published: every "
            "character outside `[A-Za-z0-9-]` of the real path replaced with `-`"
        ),
        "found": bool(where and where.is_dir()),
        "unestablished": [],
        "transcripts": [],
        "sidecars": 0,
        "tool_results": 0,
    }
    if where is None:
        # ⛔ Reported rather than guessed at: with neither name in the shell there
        # is no directory to read, and a path invented here would be a path on
        # whoever's machine wrote this module.
        answer["unestablished"].append(
            f"neither `{CONFIG_DIR}` nor `{HOME}` is in this shell, so where the "
            "harness keeps its own records cannot be derived (§ 14). Name the store "
            "on the invocation"
        )
        return answer
    if not answer["found"]:
        answer["unestablished"].append(
            f"no store directory at {where}, so what the last pass did here is unread. "
            "⛔ Not a project with no history: the derivation above is a convention and "
            "the harness is free to change it"
        )
        return answer

    files = sorted(where.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    # ⚠️ Sidecars counted and not read into the window. A delegated pass writes
    # its trace to a file of its own, so a sweep that reads only the top-level
    # file under-reports exactly the passes that were run well -- and one that
    # read every sidecar would spend the window this role exists to protect. The
    # count is what says whether there is anything there to go and read.
    answer["sidecars"] = len(list(where.glob("*/subagents/agent-*.jsonl")))
    answer["tool_results"] = len([p for p in where.glob("*/tool-results") if p.is_dir()])
    answer["transcripts_in_the_store"] = len(files)
    taken = [path for path in files if not (exclude and path.name.startswith(exclude))]
    for path in taken[:READ_BACK]:
        try:
            answer["transcripts"].append(transcript(path))
        except OSError as exc:
            answer["unestablished"].append(f"{path.name} could not be read: {exc}")
    # ⛔ The ones beyond the bound are **counted and named as dropped**, which is
    # the whole of what a cap may do in this module: a list silently cut to its
    # head reads as the whole store. Found by review on this change, measured at
    # 138 transcripts and a quarter of a million characters of JSON handed to the
    # role that exists to spend the window carefully (§ 11).
    answer["older_unread"] = max(0, len(taken) - READ_BACK)
    answer["excluded"] = exclude or None
    answer["report"] = _session_report(answer)
    return answer


def _session_report(found: dict) -> list[str]:
    lines = []
    for one in found.get("transcripts", [])[:1]:
        if one["compacted"]:
            dropped = [b.get("dropped") for b in one["boundaries"] if b.get("dropped")]
            lines.append(
                f"The last pass here was compacted {len(one['boundaries'])} time(s)"
                + (f", dropping {max(dropped)} tokens by the last of them" if dropped else "")
                + ". ⚠️ What the summary dropped is gone from the window and is still in "
                "the file, so the transcript is the evidence and the artifact is the "
                "handoff (§ 11)."
            )
        if one["ended_on"] == "an instruction":
            lines.append(
                "The last pass ends on an instruction with no reply after it, which is "
                "what a session that stopped mid-turn leaves — and what distinguishes "
                "one that stopped from one that finished and saved (§ 24)."
            )
    if not found.get("excluded") and found.get("transcripts"):
        # ⛔ The reading's own hazard, said out loud: the file a pass is writing
        # is in this store and sorts first, so a sweep that excluded nothing may
        # be reporting its own words back as the last pass's.
        lines.append(
            "No transcript was excluded, so the first of these may be the one this "
            "pass is itself writing — name it on `--exclude` to read the pass before "
            "it (§ 24)."
        )
    if found.get("older_unread"):
        lines.append(
            f"{found['older_unread']} older transcript(s) in this store were counted and "
            f"not read: this reading takes the {READ_BACK} most recent and says so rather "
            "than spending the window on the rest (§ 11)."
        )
    if found.get("sidecars"):
        lines.append(
            f"{found['sidecars']} subagent transcript(s) sit beside these, and this "
            "reading counts them rather than reading them (§ 24)."
        )
    return lines


# --- whether a file that is gone can be replayed ---------------------------


def replay(missing: str | Path, transcript_path: str | Path) -> dict:
    """Whether a working file that is gone replays from this transcript, and from what.

    ⛔ The answer is *from the transcript*, and where it is no the other place to
    look is **named**: the harness keeps the copy a file had before an edit under
    its own file-history store, which this does not read.
    """
    target = str(missing)
    real = os.path.realpath(target)
    answer: dict = {
        "missing": target,
        "exists": os.path.exists(target),
        "transcript": str(transcript_path),
        "calls": [],
        "backups": [],
        "replayable": None,
        "boundaries_before_the_first_write": 0,
    }
    # ⛔ § 24's fourth row, answered before the transcript is opened: a checkout
    # that moved or was renamed makes every path a record holds a path that does
    # not resolve, and the generic *nothing wrote it* answer would then report a
    # moved tree as a file nobody ever wrote. Found by review on this change.
    answer["resolves"] = os.path.isdir(os.path.dirname(real) or ".")
    path = Path(transcript_path)
    if not path.is_file():
        answer["unestablished"] = f"no transcript at {path}"
        answer["why"] = (
            f"no transcript at {path}, so nothing here was read and the question is "
            "unanswered rather than answered no. ⛔ Not that the file cannot be "
            "replayed: name a transcript that exists"
        )
        return answer

    boundaries = 0
    first_is_full = None
    for number, record in _records(path):
        if record.get("subtype") == BOUNDARY_TYPE:
            boundaries += 1
        if str(record.get("type", "")) == "file-history-delta":
            tracked = str(record.get("trackingPath") or "")
            parent = str((record.get("backup") or {}).get("realParentDir") or "")
            candidate = tracked if os.path.isabs(tracked) else os.path.join(parent, tracked)
            if os.path.realpath(candidate) == real:
                answer["backups"].append({
                    "version": (record.get("backup") or {}).get("version"),
                    "file": (record.get("backup") or {}).get("backupFileName"),
                })
        message = record.get("message") or {}
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict) or block.get("type") != "tool_use":
                continue
            named = WRITING_CALLS.get(str(block.get("name")))
            if not named:
                continue
            field, full = named
            where = (block.get("input") or {}).get(field)
            if not isinstance(where, str) or os.path.realpath(where) != real:
                continue
            answer["calls"].append({
                "line": number,
                "call": block.get("name"),
                "full_content": full,
                "after_a_compaction": boundaries > 0,
            })
            if first_is_full is None:
                first_is_full = full
                answer["boundaries_before_the_first_write"] = boundaries

    if not answer["calls"] and not answer["resolves"]:
        answer["replayable"] = None
        answer["why"] = (
            "the path does not resolve — the directory it names is not there — so this "
            "is a path a moved or renamed checkout left behind rather than a file "
            "nobody wrote. ⛔ Reported as that, never as the thing it pointed at being "
            "absent (§ 24): name the path under the tree as it stands now"
        )
    elif not answer["calls"]:
        answer["replayable"] = False
        answer["why"] = (
            "this transcript records no call that wrote that path, so there is nothing "
            "here to replay it from. ⛔ Not that the file never existed: a file written "
            "by another session, or by a hand at a shell, is outside this evidence"
        )
    elif first_is_full:
        answer["replayable"] = True
        answer["why"] = (
            "the first call naming that path wrote it whole, and every later one is "
            "recorded with its full input, so the file replays byte for byte by "
            f"applying the {len(answer['calls'])} call(s) below in order. ⚠️ The "
            "replay is the role's to perform or to ask about and is not performed here"
        )
    else:
        answer["replayable"] = False
        answer["why"] = (
            "the first call naming that path is an edit rather than a whole write, so "
            "the content it edited is not in this transcript and nothing here reproduces "
            f"the file. The other place to look is the harness's own file-history store "
            f"({history_root()}), which keeps the copy a file had before an edit and which "
            "does not read"
        )
    return answer


# --- the window's own reading ----------------------------------------------
#
# The field names are the harness's own, read in one direction: a payload
# carrying them is reported, and a payload carrying none of them is reported as
# that. ⚠️ **Measured absent on the harness this was written against**, which is
# why the arm is shaped around their absence rather than around their arrival:
# the figures are in `docs/configuration-surface.md`.

PRICE_EVENT = "SessionStart"
TOKENS = "context_tokens"
SINCE = "seconds_since_last_response"
EXPIRED = "prompt_cache_likely_expired"

# The sources that are a resumed window rather than a new one. A session that
# just opened has no earlier window to report, so the arm says nothing there --
# the silence of a reading that does not apply, rather than of one that failed.
RESUMED = {"resume", "fork", "compact"}

RESUME_CITATION = "schema § 24 → The window's own reading"


def resume_answer(payload: dict, *, config_for=None) -> dict:
    """The `SessionStart` answer: what this resumed window states about itself.

    ⚠️ It goes **into the session** and not to the person, which is the opposite
    of the price arm's channel one guard over: what a window costs to rewrite is
    somebody's money and their call, and how full the window is changes what the
    pass should do with it -- so the reading has to reach whoever is writing.
    """
    # ⛔ The event is required rather than defaulted: a payload naming no event
    # was answered as though it were this one, so any other event's payload
    # carrying a `source` would have had a window reading reported for it. Found
    # by review on this change.
    if str(payload.get("hook_event_name") or "") != PRICE_EVENT:
        return {}
    source = str(payload.get("source") or "")
    if source not in RESUMED:
        return {}
    loaded = config_for(payload.get("cwd")) if config_for else _config(payload.get("cwd"))
    if loaded is None:
        # ⛔ Silent, and § 7's rule is why: a project that states no
        # configuration, or whose configuration does not resolve, has agreed to
        # no role this arm could be reporting for.
        return {}
    if ROLE not in (loaded.get("carriers") or {}):
        return {}

    tokens = payload.get(TOKENS)
    since = payload.get(SINCE)
    expired = payload.get(EXPIRED)
    stated = []
    # ⛔ Both numbers accepted on the same terms. The first arm took an `int`
    # only, so a figure the harness handed over as a float was reported as *no
    # reading at all* — a stated figure reading identically to an unstated one,
    # which is the reporting failure this whole arm exists against. Found by
    # review on this change.
    if isinstance(tokens, (int, float)) and not isinstance(tokens, bool):
        stated.append(f"this window carries **{tokens}** tokens already")
    if isinstance(since, (int, float)) and not isinstance(since, bool):
        stated.append(f"the last response was {int(since)} second(s) ago")
    if isinstance(expired, bool):
        stated.append(
            "the prompt cache had likely expired" if expired
            else "the prompt cache had likely not expired"
        )
    if stated:
        said = (
            f"Session restore: this session ({source}) states that "
            + "; ".join(stated)
            + f". ⚠️ A resume into a nearly full window is a different starting position "
            f"from a resume into an empty one, and a restoring pass reports which. "
            f"({RESUME_CITATION})"
        )
    else:
        said = (
            f"Session restore: this session ({source}) was handed **no reading** of its "
            f"own window -- no token count, no time since the last response, nothing "
            f"about the prompt cache. ⛔ Not an empty window: an unstated figure and a "
            f"small one read identically, so a restoring pass reports the reading as "
            f"unhanded rather than reporting a resume as cheap. ({RESUME_CITATION})"
        )
    return {
        "hookSpecificOutput": {
            "hookEventName": PRICE_EVENT,
            "additionalContext": said,
        }
    }


CARRIER = Path(__file__).resolve().parent.parent / "hooks" / "hooks.json"


def check_the_carrier_still_calls_this(text: str) -> list[str]:
    """The carrier registers this module on the event the window reading arrives on.

    ⛔ The same shape two sibling hooks' checks have, and for the same reason: a
    carrier that stopped naming this script would leave every resumed session
    unreported with nothing saying so, and a pass that was handed no reading
    looks exactly like one that was handed an empty window.
    """
    try:
        registered = json.loads(text)
    except ValueError as error:
        return [f"the carrier is not valid JSON ({error})"]
    name = Path(__file__).name
    handlers = (registered.get("hooks") or {}).get(PRICE_EVENT)
    if not handlers:
        return [f"the carrier registers no handler for `{PRICE_EVENT}`"]
    # ⛔ Walked rather than searched as text, and the **subcommand** is what is
    # required rather than the script's name: every other subcommand here reads a
    # path it is handed, so a handler naming this module with none of them would
    # print a project's readings into every session instead of the one line this
    # event is for.
    arms = [
        arm.get("args") or []
        for entry in handlers
        for arm in (entry.get("hooks") or [])
    ]
    calls = [args for args in arms if any(name in str(part) for part in args)]
    problems = []
    if not calls:
        problems.append(f"no `{PRICE_EVENT}` handler calls `{name}`")
    elif not any("resume" in [str(part) for part in args] for args in calls):
        problems.append(
            f"the `{PRICE_EVENT}` handler calls `{name}` without the `resume` "
            "subcommand, so the event's own payload reaches no arm"
        )
    called = json.dumps(calls)
    if calls and "${CLAUDE_PLUGIN_ROOT}" not in called:
        problems.append(
            f"a `{PRICE_EVENT}` handler names this script by a path the plugin root does "
            "not expand — the handler must address it through `${CLAUDE_PLUGIN_ROOT}`"
        )
    return problems


def _config(cwd: str | None):
    """The project's configuration, or None where there is none to read."""
    where = cwd or "."
    try:
        if not config.configured(where):
            return None
        return config.load(where)
    except (config.ConfigError, OSError):
        return None


# --- the self-test ---------------------------------------------------------


def _snapshot(root: str | Path) -> dict[str, tuple[int, str]]:
    """Every path under a root, by (size, digest). The writes-nothing assertion.

    ⛔ On the bytes and not on a modification time: a file rewritten with its own
    contents is not a file this module left alone, and a stat-based snapshot
    would call a rewritten one changed and a same-second one unchanged.

    ⛔ **Directories are in it**, which is not where this started: a snapshot of
    files alone passes a module that created an empty directory, and creating the
    store a reading could not find is exactly the shape that would. Found by
    planting that write and watching the general arm stay green while only the
    one named assertion beside it reddened.

    ⛔ **And every other kind of entry is in it too** — a symlink, a socket, a
    fifo — for the same reason one step over: a snapshot that recorded files and
    directories alone stayed green against a planted symlink, which is a write
    like any other. Found by review on this change, reproduced by compiling a
    mutant that plants one.
    """
    import hashlib  # noqa: PLC0415 -- the one arm that needs a digest

    found = {}
    for path in sorted(Path(root).rglob("*")):
        # ⛔ The symlink arm first: a link to a directory answers `is_dir()`, and
        # a dangling one answers neither, which is how it went unrecorded.
        if path.is_symlink():
            found[str(path.relative_to(root)) + "@"] = (0, f"a link to {os.readlink(path)}")
            continue
        if path.is_dir():
            found[str(path.relative_to(root)) + "/"] = (0, "a directory")
            continue
        if path.is_file():
            try:
                blob = path.read_bytes()
            except OSError:
                continue
            found[str(path.relative_to(root))] = (
                len(blob), hashlib.sha256(blob).hexdigest()
            )
            continue
        # Anything else that exists -- a socket, a fifo, a device -- recorded as
        # being there at all, which is the whole of what this assertion needs.
        found[str(path.relative_to(root)) + "?"] = (0, "an entry of another kind")
    return found


# The one path a read of a working tree may legitimately touch: git's own stat
# cache. ⛔ Named rather than tolerated generally, so a module that wrote
# anything else would redden.
GITS_OWN = {".git/index"}


def _a_world(where: Path, branch: str = "feature/31-a-branch") -> tuple[str, str]:
    """(a bare repository standing in for the host, a clone on a branch of its own).

    Real repositories and no stand-in: what is in question is what git says about
    a position, and a fake would assert the fake's own idea of one.
    """
    import subprocess  # noqa: PLC0415 -- the fixture's own git, not the module's

    def run(*args: str, root: Path | None = None) -> None:
        proc = subprocess.run(
            ["git", *(["-C", str(root)] if root else []), *args],
            capture_output=True, text=True,
        )
        if proc.returncode != 0:
            raise AssertionError(
                f"the fixture's `git {' '.join(args)}` failed: "
                f"{proc.stderr.strip() or proc.stdout.strip()}"
            )

    where = where.resolve()
    origin = where / "origin.git"
    run("init", "--quiet", "--bare", "--initial-branch=main", str(origin))
    tree = where / "a-tree"
    run("clone", "--quiet", str(origin), str(tree))
    for key, value in (("user.email", "a@tree"), ("user.name", "A Tree")):
        run("config", key, value, root=tree)
    (tree / "base.txt").write_text("a line\n", encoding="utf-8")
    run("add", "base.txt", root=tree)
    run("commit", "--quiet", "-m", "add base.txt", root=tree)
    run("branch", "-M", "main", root=tree)
    run("push", "--quiet", "origin", "main", root=tree)
    run("checkout", "--quiet", "-b", branch, root=tree)
    return str(origin), str(tree)


def _a_commit(root: str, name: str, text: str = "a line\n") -> None:
    import subprocess  # noqa: PLC0415 -- the fixture's own git

    (Path(root) / name).write_text(text, encoding="utf-8")
    for args in (["add", name], ["commit", "--quiet", "-m", f"add {name}"]):
        proc = subprocess.run(["git", "-C", root, *args], capture_output=True, text=True)
        if proc.returncode != 0:
            raise AssertionError(f"the fixture could not commit {name}: {proc.stderr.strip()}")


def _a_transcript(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record) + "\n")


def _a_call(name: str, field: str, where: str, **rest) -> dict:
    return {
        "type": "assistant",
        "message": {"role": "assistant", "content": [
            {"type": "tool_use", "name": name, "input": {field: where, **rest}},
        ]},
    }


def _a_turn(kind: str, text: str) -> dict:
    return {"type": kind, "message": {"role": kind, "content": [{"type": "text", "text": text}]}}


def _a_boundary(dropped: int = 600000) -> list[dict]:
    return [
        {"type": "system", "subtype": BOUNDARY_TYPE, "compactMetadata": {
            "trigger": "manual", "preTokens": 617688, "postTokens": 14285,
            "cumulativeDroppedTokens": dropped,
        }},
        {"type": "user", SUMMARY_FLAG: True, "message": {
            "role": "user", "content": "This session is being continued from a previous…",
        }},
    ]


def _a_payload(source: str = "resume", **fields) -> dict:
    return {"hook_event_name": PRICE_EVENT, "cwd": ".", "source": source, **fields}


def _a_project_without_the_role(where: Path) -> Path:
    """A project that states a whole configuration and maps no restoring role.

    ⛔ Built from a shipped example rather than from a few keys written here: the
    reader refuses an incomplete configuration before it ever looks at
    `carriers`, so a hand-written fixture asserts the refusal instead of the
    arm. ⚠️ And the example is **read for its own sake** — an example that began
    mapping this role would redden this arm rather than passing it, which is the
    direction that fails safe.
    """
    root = where / "maps-no-restoring-role"
    stated = root / config.CONFIG_PATH
    stated.parent.mkdir(parents=True, exist_ok=True)
    example = sorted(Path(config.EXAMPLES).glob("*.yaml"))[0]
    stated.write_text(example.read_text(encoding="utf-8"), encoding="utf-8")
    return root


def self_test() -> int:  # noqa: PLR0915 -- one suite, read top to bottom
    import io  # noqa: PLC0415 -- the arm that hands `main` a payload
    import tempfile  # noqa: PLC0415 -- the arms that need a tree

    failures: list[str] = []
    ran = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal ran
        ran += 1
        if condition:
            print(f"  ok    {label}")
        else:
            failures.append(label)
            print(f"  FAIL  {label}" + (f": {detail}" if detail else ""))

    live = config.load(config.REPO_ROOT)

    print("the readings, in the procedure's order rather than a configuration's")
    taken = readings(live)
    check(
        "every reading the procedure states comes back, in its order",
        [entry["reading"] for entry in taken] == ORDER,
        f"came back {[e['reading'] for e in taken]!r}",
    )
    check(
        "and each one names what it reads",
        all(entry["reads"] for entry in taken),
        f"came back {taken!r}",
    )
    check(
        "every reading this module places names what it reads",
        set(ORDER) <= set(READS),
        f"placed {ORDER!r} and names {sorted(READS)!r}",
    )
    # ⛔ Stated as an equivalence rather than as *memory is unavailable*, so the
    # arm keeps holding the day that reading acquires a store.
    check(
        "a reading with no store is reported unavailable rather than dropped",
        all(
            entry["available"] is False
            for entry in taken
            if entry["reading"] in WITHOUT_A_STORE
        ),
        f"came back {taken!r}",
    )
    check(
        "the reading nothing here can answer comes back unanswered, not absent",
        all(
            entry["available"] is None
            for entry in taken
            if entry["reading"] in ANSWERED_ELSEWHERE
        ),
        f"came back {taken!r}",
    )
    check(
        "the storeless reading is one the procedure places",
        WITHOUT_A_STORE | ANSWERED_ELSEWHERE <= set(ORDER),
        f"{WITHOUT_A_STORE | ANSWERED_ELSEWHERE!r} against {ORDER!r}",
    )
    # ⛔ The configuration reader reports the same absence for the third that
    # writes that store, and nothing but this holds the two statements to each
    # other: a reading this module calls unavailable while the reader reports it
    # carried is a role told to skip a reading that can run.
    check(
        "the reader reports the same store absent",
        any("memory" in line and "unavailable" in line for line in live.unavailable()),
        f"reported {live.unavailable()!r}",
    )
    said = report_for(live, taken)
    check(
        "this project's own absences are each said out loud",
        any("#35" in line for line in said) and any("mechanics" in line for line in said),
        f"said {said!r}",
    )

    # ⛔ The other arm of the environment reading, which this project cannot
    # reach: where the project does point at a setup, the pointer's own value is
    # what the role is handed — a report naming only that one exists leaves the
    # role with nothing to read and no key it may read it from.
    class _Points:
        def __init__(self, at):
            self.at = at

        def get(self, key):
            if key == "branch_model.mechanics":
                return self.at
            return {"carriers": {ROLE: "skill"}}.get(key)

        def unavailable(self):
            return []

    pointed = _Points("tools/stand-up-the-stack")
    check(
        "a project that points at its own setup is handed the pointer's value",
        any("tools/stand-up-the-stack" in line
            for line in report_for(pointed, readings(pointed))),
        f"said {report_for(pointed, readings(pointed))!r}",
    )
    check(
        "and a tree-per-item project is told to sweep the checkout's store too",
        any("checkout" in line for line in said),
        f"said {said!r}",
    )
    # The item reading's availability is the port's answer and never a second one.
    class _Says:
        def __init__(self, answer):
            self.answer = answer

        def implements(self, _operation):
            return self.answer

    check(
        "the item reading follows the port rather than answering for it",
        readings(live, tracker=_Says(False))[1]["available"] is False
        and readings(live, tracker=_Says(True))[1]["available"] is True,
        f"came back {readings(live, tracker=_Says(False))[1]!r}",
    )
    # ⛔ And each of those states has its own line in the report, asserted on the
    # state rather than on the happy path: an item the port cannot read and an
    # item nothing asked about are different sentences to whoever reads this.
    unreadable = report_for(live, readings(live, tracker=_Says(False)))
    check(
        "an item the port cannot read is reported as unread, not as empty",
        any("names the item" in line and "unread" in line for line in unreadable),
        f"said {unreadable!r}",
    )
    check(
        "and an item nothing asked about is reported as unanswered",
        any("could not be asked about" in line for line in said),
        f"said {said!r}",
    )

    print()
    print("where the work is: the two readings that look like nothing to do")
    with tempfile.TemporaryDirectory() as directory:
        _origin, tree = _a_world(Path(directory))
        found = position(tree, base="main")
        check("a fresh branch names itself", found.get("branch") == "feature/31-a-branch")
        check(
            "and the item its name carries",
            found.get("item_in_branch") == "31",
            f"came back {found.get('item_in_branch')!r}",
        )
        check(
            "a branch with no ref on the remote is reported as unpublished",
            found.get("unpushed_branch") is True and found.get("published_ref") is None,
            f"came back {found!r}",
        )
        check(
            "and the position names the fetch it did not do",
            "nothing here fetched" in found.get("as_of", ""),
            f"came back {found.get('as_of')!r}",
        )

        _a_commit(tree, "work.txt")
        found = position(tree, base="main")
        check(
            "a commit that is nowhere else is counted as unpushed",
            found.get("unpushed_count") == 1,
            f"came back {found.get('unpushed_count')!r} from {found.get('unpushed')!r}",
        )
        check(
            "and named, not only counted",
            any("work.txt" in line for line in found.get("unpushed", [])),
            f"came back {found.get('unpushed')!r}",
        )
        check(
            "and the report says so in words",
            any("nothing outside this tree has" in line for line in found.get("report", [])),
            f"reported {found.get('report')!r}",
        )
        check(
            "the position against the base is read",
            found.get("ahead_of_base") == 1 and found.get("behind_base") == 0,
            f"came back {found!r}",
        )

        import subprocess  # noqa: PLC0415 -- the fixture's own git

        subprocess.run(["git", "-C", tree, "push", "--quiet", "-u", "origin",
                        "feature/31-a-branch"], capture_output=True, text=True, check=True)
        found = position(tree, base="main")
        check(
            "a pushed branch has nothing unpushed",
            found.get("unpushed_count") == 0 and found.get("published_ref")
            == "origin/feature/31-a-branch",
            f"came back {found!r}",
        )
        _a_commit(tree, "more.txt")
        found = position(tree, base="main")
        check(
            "and a commit after the push is unpushed again",
            found.get("unpushed_count") == 1 and found.get("ahead_of_published") == 1,
            f"came back {found!r}",
        )
        # ⛔ The behind-the-remote arm, planted by moving the published ref from
        # a second clone: the one direction a sweep reading only this tree cannot
        # see, and the one that reads as nothing to do.
        other = Path(directory) / "another-clone"
        subprocess.run(["git", "clone", "--quiet", "-b", "feature/31-a-branch",
                        _origin, str(other)], capture_output=True, text=True, check=True)
        for key, value in (("user.email", "b@tree"), ("user.name", "B Tree")):
            subprocess.run(["git", "-C", str(other), "config", key, value], check=True)
        _a_commit(str(other), "theirs.txt")
        subprocess.run(["git", "-C", str(other), "push", "--quiet", "origin",
                        "feature/31-a-branch"], capture_output=True, text=True, check=True)
        subprocess.run(["git", "-C", tree, "fetch", "--quiet", "origin"],
                       capture_output=True, text=True, check=True)
        found = position(tree, base="main")
        check(
            "a branch behind its own published ref is reported as behind",
            found.get("behind_published") == 1,
            f"came back {found!r}",
        )
        check(
            "and the report names what moved the claim's ref",
            any("moved the claim" in line for line in found.get("report", [])),
            f"reported {found.get('report')!r}",
        )
        # ⛔ The hazard § 10 names: an upstream pointing at the base.
        subprocess.run(["git", "-C", tree, "branch", "--set-upstream-to", "origin/main"],
                       capture_output=True, text=True, check=True)
        found = position(tree, base="main")
        check(
            "an upstream pointing at the base is named as the hazard it is",
            found.get("upstream_is_base") is True
            and any("writes to the base" in line for line in found.get("report", [])),
            f"came back {found!r}",
        )
        (Path(tree) / "untracked.txt").write_text("not committed\n", encoding="utf-8")
        found = position(tree, base="main")
        check(
            "an untracked file is in the dirty reading",
            any("untracked.txt" in line for line in found.get("dirty", [])),
            f"came back {found.get('dirty')!r}",
        )
        check(
            "and the report states that nothing was moved",
            any("Nothing was stashed" in line for line in found.get("report", [])),
            f"reported {found.get('report')!r}",
        )
        # ⚠️ The green side of the same arm: a path that is not a repository is
        # reported as that rather than raising out of a read-only sweep.
        plain = Path(directory) / "not-a-repository"
        plain.mkdir()
        found = position(str(plain))
        check(
            "a path that is no repository is reported, not raised",
            any("not a git repository" in line for line in found.get("unestablished", [])),
            f"came back {found!r}",
        )
        # ⛔ The four readings a position can be wrong about rather than silent
        # on, each planted on a real repository because each was found by review
        # reporting something false with a straight face.
        empty_repo = Path(directory) / "no-commit-yet"
        subprocess.run(["git", "init", "--quiet", "-b", "main", str(empty_repo)], check=True)
        found = position(str(empty_repo))
        check(
            "a repository with no commit is reported as that, not as no repository",
            any("no commit on its checked-out branch" in line
                for line in found.get("unestablished", []))
            and not any("not a git repository" in line
                        for line in found.get("unestablished", [])),
            f"came back {found!r}",
        )
        check(
            "and it still names the branch that exists",
            found.get("branch") == "main",
            f"came back {found.get('branch')!r}",
        )
        # A repository with no remote: the one derivation of a base falls back to
        # this branch, and counting a branch against itself is a reading nobody
        # took rather than a pair of zeroes.
        alone = Path(directory) / "no-remote"
        subprocess.run(["git", "init", "--quiet", "-b", "main", str(alone)], check=True)
        for key, value in (("user.email", "c@tree"), ("user.name", "C Tree")):
            subprocess.run(["git", "-C", str(alone), "config", key, value], check=True)
        _a_commit(str(alone), "first.txt")
        subprocess.run(["git", "-C", str(alone), "checkout", "--quiet", "-b",
                        "feature/7-alone"], check=True)
        _a_commit(str(alone), "second.txt")
        found = position(str(alone))
        check(
            "a repository with no remote reports the base as unread, never as zero",
            "behind_base" not in found and "ahead_of_base" not in found
            and any("which is this branch" in line
                    for line in found.get("unestablished", [])),
            f"came back {found!r}",
        )
        check(
            "and its own commits are still reported as unpushed",
            found.get("unpushed_count") == 2,
            f"came back {found.get('unpushed_count')!r}",
        )
        # A detached head: every other reading is about a position nothing owns.
        sha = subprocess.run(["git", "-C", tree, "rev-parse", "HEAD"],
                             capture_output=True, text=True, check=True).stdout.strip()
        subprocess.run(["git", "-C", tree, "checkout", "--quiet", "--detach", sha],
                       capture_output=True, text=True, check=True)
        found = position(tree, base="main")
        check(
            "a detached tree is reported as on no branch at all",
            found.get("detached") is True
            and any("no branch at all" in line for line in found.get("report", [])),
            f"came back {found!r}",
        )
        subprocess.run(["git", "-C", tree, "checkout", "--quiet", "feature/31-a-branch"],
                       capture_output=True, text=True, check=True)
        # A base ref that is not there at all, which is a reading unread rather
        # than a position of zero.
        found = position(tree, base="no-such-base")
        check(
            "a base ref this tree does not have is reported unread",
            "behind_base" not in found
            and any("could be counted" in line for line in found.get("unestablished", [])),
            f"came back {found!r}",
        )

    print()
    print("what the last pass was doing, and what a compaction left of it")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        work = root / "a-tree"
        work.mkdir()
        store = root / "store"
        derived = store_dir_for(work, store)
        check(
            "the store directory is derived by the harness's own convention",
            derived.name == re.sub(r"[^A-Za-z0-9-]", "-", os.path.realpath(str(work))),
            f"came back {derived.name!r}",
        )
        # ⛔ The derivation a role actually gets, with no store named: every
        # assertion passing `--store` left the production path asserted nowhere.
        # Found by review on this change.
        production = store_dir_for(work)
        check(
            "and with no store named it lands under the harness's own directory",
            production is not None
            and production.parent == (harness_dir() or Path()) / SESSIONS_UNDER
            and production.name == derived.name,
            f"came back {production!r} against {harness_dir()!r}",
        )
        # The two text readings, each asserted on the shape the live store has
        # rather than on the fixture's convenience.
        check(
            "a record whose content is a bare string is read",
            _text_of({"message": {"content": "a plain string"}}) == "a plain string",
        )
        check(
            "a span the harness appends to a real turn is stripped from it",
            _text_of({"message": {"content": [
                {"type": "text", "text": "do the work <system-reminder>not this</system-reminder>"},
            ]}}) == "do the work",
            f"came back {_text_of({'message': {'content': []}})!r}",
        )
        check(
            "and a quotation longer than the bound says it was trimmed",
            _trim("x" * (QUOTED + 50)).endswith(f"(trimmed at {QUOTED} characters)"),
            f"came back {_trim('x' * (QUOTED + 50))[-60:]!r}",
        )
        empty = session(work, store=store)
        check(
            "a store that is not there is reported as not found",
            empty["found"] is False
            and any("no store directory" in line for line in empty["unestablished"]),
            f"came back {empty!r}",
        )
        check(
            "⛔ and never as a project with no history",
            any("Not a project with no history" in line for line in empty["unestablished"]),
            f"came back {empty['unestablished']!r}",
        )

        # ⛔ The store root is the harness's and is read out of the shell, so the
        # arm where the shell holds neither name is asserted rather than assumed:
        # a module that fell back to a path of its own would be writing down a
        # path on whoever's machine it was written on.
        held = {name: os.environ.pop(name, None) for name in (CONFIG_DIR, HOME)}
        try:
            check(
                "with neither name in the shell there is no store to derive",
                harness_dir() is None and store_dir_for(work) is None,
                f"came back {harness_dir()!r}",
            )
            nowhere = session(work)
            check(
                "and the reading is reported as underivable, naming both names",
                any(
                    CONFIG_DIR in line and HOME in line
                    for line in nowhere["unestablished"]
                ),
                f"came back {nowhere!r}",
            )
            check(
                "while a store named on the invocation is read anyway",
                store_dir_for(work, store) is not None,
                "the override is what a shell holding neither name leaves a person",
            )
        finally:
            for name, value in held.items():
                if value is not None:
                    os.environ[name] = value

        _a_transcript(derived / "aaaa.jsonl", [
            _a_turn("user", "take the next item"),
            _a_call("Write", "file_path", str(work / "notes.md"), content="first\n"),
            *_a_boundary(dropped=603403),
            _a_turn("user", "carry on"),
            _a_turn("assistant", "the item is implemented and the tree is clean"),
        ])
        (derived / "aaaa" / "subagents").mkdir(parents=True)
        (derived / "aaaa" / "subagents" / "agent-1.jsonl").write_text("", encoding="utf-8")
        (derived / "aaaa" / "tool-results").mkdir(parents=True)
        read = session(work, store=store)
        check("the store is found once it is there", read["found"] is True)
        one = read["transcripts"][0]
        check(
            "the last instruction and the last reply are both read",
            one["last_instruction"] == "carry on"
            and one["last_reply"].startswith("the item is implemented"),
            f"came back {one!r}",
        )
        check(
            "a compaction boundary is read with what it dropped",
            one["compacted"] is True and one["boundaries"][0]["dropped"] == 603403
            and one["boundaries"][0]["trigger"] == "manual",
            f"came back {one['boundaries']!r}",
        )
        check(
            "and the summary record is not read as the last instruction",
            "continued from a previous" not in str(one["last_instruction"]),
            f"came back {one['last_instruction']!r}",
        )
        check(
            "the sidecars are counted rather than read",
            read["sidecars"] == 1 and read["tool_results"] == 1,
            f"came back {read!r}",
        )
        check(
            "and the report says that is what it did",
            any("counts them rather than reading" in line for line in read["report"]),
            f"reported {read['report']!r}",
        )
        check(
            "and each transcript carries the path the replay reading takes",
            one["path"].endswith("aaaa.jsonl") and os.path.isabs(one["path"]),
            f"came back {one.get('path')!r}",
        )
        check(
            "a pass that excluded nothing is told the first file may be its own",
            any("may be the one this" in line for line in read["report"]),
            f"reported {read['report']!r}",
        )
        # ⛔ What the harness writes as a `user` record that no person typed. The
        # plant is the shape measured on this repository's own store, where 78 of
        # 138 transcripts ended on one and the reading took it as the last
        # instruction.
        _a_transcript(derived / "bbbb.jsonl", [
            _a_turn("user", "take the next item"),
            _a_turn("assistant", "taken, and the tree is cut"),
            _a_turn("user", "<command-name>/exit</command-name>"),
            {"type": "user", META: True, "message": {
                "role": "user", "content": "<local-command-caveat>Caveat…</local-command-caveat>",
            }},
            _a_turn("user", "<local-command-stdout>Bye!</local-command-stdout>"),
        ])
        farewell = session(work, store=store, exclude="aaaa")["transcripts"][0]
        check(
            "the harness's own plumbing is not read as the last instruction",
            farewell["last_instruction"] == "take the next item",
            f"came back {farewell['last_instruction']!r}",
        )
        check(
            "and a session that finished on a reply is not reported as a stop",
            farewell["ended_on"] == "a reply"
            and not any("stopped mid-turn" in line
                        for line in session(work, store=store, exclude="aaaa")["report"]),
            f"came back {farewell['ended_on']!r}",
        )
        # ⛔ A session that died on its twenty-first turn carries twenty replies,
        # so the tell is the order the records end in and never two last values.
        _a_transcript(derived / "cccc.jsonl", [
            _a_turn("user", "the first part"),
            _a_turn("assistant", "done the first part"),
            _a_turn("user", "now do the second part"),
        ])
        stopped = session(work, store=store, exclude="aaaa")
        check(
            "an instruction with a reply before it and none after is a stop mid-turn",
            stopped["transcripts"][0]["ended_on"] == "an instruction"
            and stopped["transcripts"][0]["last_reply"] is not None
            and any("stopped mid-turn" in line for line in stopped["report"]),
            f"came back {stopped['transcripts'][0]!r}",
        )
        # ⚠️ A half-written last line is legitimate in a live transcript, and ⛔ a
        # line cut **inside a character** is the shape that raised rather than
        # being skipped: this tree's own transcripts are full of multi-byte
        # markers. Found by review on this change.
        for tail in (b'{"type": "user", "message"', '{"x": "⛔'.encode()[:-1]):
            with (derived / "cccc.jsonl").open("ab") as handle:
                handle.write(tail)
            check(
                f"a last line cut at {len(tail)} bytes is skipped rather than fatal",
                session(work, store=store, exclude="aaaa")["transcripts"][0]["records"] == 3,
                "a transcript being appended to while it is read has a partial last line",
            )
        # The cap, and that what is beyond it is counted rather than dropped.
        for name in ("dddd", "eeee", "ffff"):
            _a_transcript(derived / f"{name}.jsonl", [_a_turn("user", name)])
        capped = session(work, store=store)
        check(
            f"a store with more transcripts than the bound reads {READ_BACK}",
            len(capped["transcripts"]) == READ_BACK
            and capped["transcripts_in_the_store"] == 6,
            f"came back {len(capped['transcripts'])!r} of "
            f"{capped.get('transcripts_in_the_store')!r}",
        )
        check(
            "and names the older ones as counted and unread",
            capped["older_unread"] == 3
            and any("counted and" in line for line in capped["report"]),
            f"came back {capped!r}",
        )

        print()
        print("whether a file that is gone replays, and from what")
        gone = work / "notes.md"
        answer = replay(gone, derived / "aaaa.jsonl")
        check(
            "a file first written whole replays byte for byte",
            answer["replayable"] is True and len(answer["calls"]) == 1,
            f"came back {answer!r}",
        )
        check(
            "and the file being missing is stated rather than assumed",
            answer["exists"] is False,
            f"came back {answer['exists']!r}",
        )
        # ⛔ The measured fact the whole answer rests on: a compaction appends,
        # so a write **before** a boundary is still in the file after it.
        _a_transcript(derived / "replay-after-a-boundary.jsonl", [
            _a_call("Write", "file_path", str(gone), content="first\n"),
            *_a_boundary(),
            _a_turn("user", "and on we go"),
        ])
        after = replay(gone, derived / "replay-after-a-boundary.jsonl")
        check(
            "a write before a compaction replays after it",
            after["replayable"] is True and after["boundaries_before_the_first_write"] == 0,
            f"came back {after!r}",
        )
        _a_transcript(derived / "replay-edited-only.jsonl", [
            _a_call("Edit", "file_path", str(gone), old_string="a", new_string="b"),
        ])
        edited = replay(gone, derived / "replay-edited-only.jsonl")
        check(
            "a file only ever edited does not replay from the transcript",
            edited["replayable"] is False,
            f"came back {edited!r}",
        )
        check(
            "and the other place to look is named",
            "file-history" in str(edited.get("why")),
            f"came back {edited.get('why')!r}",
        )
        _a_transcript(derived / "replay-wrote-nothing.jsonl", [_a_turn("user", "nothing was written")])
        silent = replay(gone, derived / "replay-wrote-nothing.jsonl")
        check(
            "a transcript that wrote it nowhere says so, and claims nothing wider",
            silent["replayable"] is False and "never existed" in str(silent.get("why")),
            f"came back {silent!r}",
        )
        nowhere = replay(gone, derived / "no-such.jsonl")
        check(
            "a transcript that is not there is reported, not raised",
            "unestablished" in nowhere,
            "a path that is not a transcript is an answer rather than a crash",
        )
        check(
            "⛔ and it is unanswered rather than answered no",
            nowhere["replayable"] is None and "unanswered" in str(nowhere.get("why")),
            f"came back {nowhere!r}",
        )
        # ⛔ The discriminator of the whole reading: a call that wrote **another**
        # path answers nothing about this one. Planted because deleting the path
        # comparison left every assertion green. Found by review on this change.
        _a_transcript(derived / "replay-another-path.jsonl", [
            _a_call("Write", "file_path", str(work / "something-else.md"), content="x\n"),
        ])
        elsewhere = replay(gone, derived / "replay-another-path.jsonl")
        check(
            "a whole write of another path is not read as this file's",
            elsewhere["replayable"] is False and not elsewhere["calls"],
            f"came back {elsewhere!r}",
        )
        # ⛔ § 24's fourth row: a path whose directory is not there is a moved or
        # renamed checkout rather than a file nobody wrote.
        moved = replay(root / "a-tree-that-moved" / "notes.md",
                       derived / "replay-wrote-nothing.jsonl")
        check(
            "a path that does not resolve is reported as that, not as never written",
            moved["replayable"] is None and moved["resolves"] is False
            and "moved or renamed" in str(moved.get("why")),
            f"came back {moved!r}",
        )
        # The backup record the harness writes beside an edit, read as the second
        # source rather than as the content itself.
        _a_transcript(derived / "replay-with-a-backup.jsonl", [
            {"type": "file-history-delta", "trackingPath": "notes.md",
             "backup": {"backupFileName": "abc@v1", "version": 1,
                        "realParentDir": str(work)}},
            _a_call("Edit", "file_path", str(gone), old_string="a", new_string="b"),
        ])
        backed = replay(gone, derived / "replay-with-a-backup.jsonl")
        check(
            "a backup record for that path is reported beside the answer",
            backed["backups"] and backed["backups"][0]["file"] == "abc@v1",
            f"came back {backed['backups']!r}",
        )

    print()
    print("the window's own reading, and the absence that is not an empty window")
    priced = _a_payload(**{TOKENS: 617688, SINCE: 4000, EXPIRED: True})
    mapped = config.load(config.REPO_ROOT)
    answered = resume_answer(priced, config_for=lambda _cwd: mapped)
    text = str(answered.get("hookSpecificOutput", {}).get("additionalContext", ""))
    check("a payload that states a window is reported", bool(text))
    check("the figure itself is in it", "617688" in text, text[:160])
    check("the time since the last response is in it", "4000 second" in text, text[:160])
    check("the prompt cache is in it", "cache had likely expired" in text, text[:160])
    check("the rule is cited", RESUME_CITATION in text, text[:160])
    check(
        "⛔ and it reaches the session rather than the person",
        "hookSpecificOutput" in answered and "systemMessage" not in answered,
        f"came back {sorted(answered)!r}",
    )
    silent = resume_answer(_a_payload(source="startup", **{TOKENS: 10}),
                           config_for=lambda _cwd: mapped)
    check(
        "a session that just opened is said nothing to",
        silent == {},
        f"came back {silent!r}",
    )
    none_of_it = resume_answer(_a_payload(), config_for=lambda _cwd: mapped)
    said = str(none_of_it.get("hookSpecificOutput", {}).get("additionalContext", ""))
    check("a resume the harness stated nothing about is reported", bool(said))
    check(
        "⛔ as unhanded rather than as an empty window",
        "no reading" in said and "read identically" in said,
        said[:200],
    )
    check(
        "another event's payload is not answered at all",
        resume_answer({"hook_event_name": "Stop", "source": "resume"},
                      config_for=lambda _cwd: mapped) == {},
    )
    check(
        "⛔ and a payload naming no event is not answered as though it were this one",
        resume_answer({"source": "resume", TOKENS: 10},
                      config_for=lambda _cwd: mapped) == {},
        "the event was defaulted, so any other event's payload carrying a source got "
        "a window reading reported for it",
    )
    # ⛔ A figure stated as a float is a figure, and reporting it as *no reading*
    # is the one failure this arm exists against. Found by review on this change.
    floated = resume_answer(_a_payload(**{TOKENS: 617688.0}), config_for=lambda _cwd: mapped)
    check(
        "a token count handed over as a float is reported as the figure it is",
        "617688" in str(floated.get("hookSpecificOutput", {}).get("additionalContext", "")),
        f"came back {floated!r}",
    )
    check(
        "a project that states no configuration is said nothing to",
        resume_answer(priced, config_for=lambda _cwd: None) == {},
        "§ 7: a project that configures nothing has agreed to no rule this reports for",
    )
    # ⛔ The role being mapped is what the arm reports for, asserted in both
    # directions: an arm that answered for a project mapping no restoring role
    # would be putting a reading into a session nothing there reads.
    class _Maps:
        def __init__(self, roles):
            self.roles = roles

        def get(self, key):
            return self.roles if key == "carriers" else None

    check(
        "a project mapping no restoring role is said nothing to",
        resume_answer(priced, config_for=lambda _cwd: _Maps({"start": "skill"})) == {},
        "the arm reports for a role the project maps, by § 7",
    )
    check(
        "and one that maps it is",
        bool(resume_answer(priced, config_for=lambda _cwd: _Maps({ROLE: "skill"}))),
    )
    check(
        "this project maps the role, so the arm above was asked something live",
        ROLE in (mapped.get("carriers") or {}),
        f"carriers are {sorted(mapped.get('carriers') or {})!r}",
    )
    # ⛔ And the carrier still calls this, which is what makes the arm above reach
    # a session at all. Asserted in both directions: a carrier that names the
    # script and not the subcommand is the shape that passes a text search.
    registered = CARRIER.read_text(encoding="utf-8")
    check(
        "the carrier registers this module on the event it answers",
        not check_the_carrier_still_calls_this(registered),
        f"reported {check_the_carrier_still_calls_this(registered)!r}",
    )
    for label, planted, named in (
        ("a carrier that registers the event and not this module",
         json.dumps({"hooks": {PRICE_EVENT: [{"hooks": [
             {"type": "command", "command": "python3", "args": ["elsewhere.py"]}]}]}}),
         "calls"),
        ("a carrier that calls this module with no subcommand",
         json.dumps({"hooks": {PRICE_EVENT: [{"hooks": [
             {"type": "command", "command": "python3",
              "args": ["${CLAUDE_PLUGIN_ROOT}/scripts/load.py"]}]}]}}),
         "without the `resume` subcommand"),
        ("a carrier that drops the event altogether", json.dumps({"hooks": {}}),
         "registers no handler"),
        ("a carrier naming this module by a path the plugin root does not expand",
         json.dumps({"hooks": {PRICE_EVENT: [{"hooks": [
             {"type": "command", "command": "python3",
              "args": ["plugins/mjolnir/scripts/load.py", "resume"]}]}]}}),
         "plugin root does not expand"),
        ("a carrier that is not valid JSON", "{", "not valid JSON"),
    ):
        found = check_the_carrier_still_calls_this(planted)
        check(
            f"{label} is refused, naming it",
            any(named in problem for problem in found),
            f"reported {found!r}",
        )

    print()
    print("⛔ every subcommand writes nothing, run where a naive one would have")
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        _origin, tree = _a_world(root / "world")
        _a_commit(tree, "work.txt")
        work = root / "a-tree"
        work.mkdir()
        store = root / "store"
        derived = store_dir_for(work, store)
        _a_transcript(derived / "aaaa.jsonl", [
            _a_turn("user", "take the next item"),
            _a_call("Write", "file_path", str(work / "gone.md"), content="first\n"),
        ])
        # A store that does not exist, a working file that is missing, and an
        # artifact a resuming pass would be tempted to create: the three places a
        # sweep that *restored* rather than reported would write.
        absent_store = root / "no-store-here"
        missing = work / "gone.md"
        before = _snapshot(root)
        position(tree, base="main")
        session(work, store=store)
        session(work, store=absent_store)
        replay(missing, derived / "aaaa.jsonl")
        replay(missing, absent_store / "no-such.jsonl")
        readings(mapped)
        resume_answer(priced, config_for=lambda _cwd: mapped)
        after = _snapshot(root)
        created = sorted(set(after) - set(before))
        removed = sorted(set(before) - set(after))
        changed = sorted(
            path for path in set(before) & set(after) if before[path] != after[path]
        )
        check(
            "nothing is created anywhere, the store that is absent included",
            not created,
            f"created {created!r}",
        )
        check("and nothing is removed", not removed, f"removed {removed!r}")
        check(
            "and nothing but git's own index differs",
            all(path.endswith(tuple(GITS_OWN)) for path in changed),
            f"changed {changed!r}",
        )
        check(
            "the missing file is still missing, so nothing restored it",
            not missing.exists() and not absent_store.exists(),
            "a sweep that helpfully restored what it found missing has decided something",
        )
        # ⛔ The assertion is believed only once it has been shown it can fail,
        # and it is shown on every kind of entry rather than on a file alone: a
        # files-and-directories snapshot stayed green against a planted symlink.
        # Found by review on this change.
        for label, plant in (
            ("a file", lambda: (root / "planted.txt").write_text("x", encoding="utf-8")),
            ("a directory", lambda: (root / "planted-dir").mkdir()),
            ("a symlink to nowhere", lambda: os.symlink("nowhere", root / "planted-link")),
        ):
            plant()
            planted = _snapshot(root)
            check(
                f"the snapshot sees {label} appear",
                sorted(set(planted) - set(after)),
                f"{label} was planted and the snapshot reported no difference",
            )
            after = planted

        print()
        print("⛔ and the same invocation twice gives the same report")
        check(
            "the position is the same read twice",
            json.dumps(position(tree, base="main"), sort_keys=True)
            == json.dumps(position(tree, base="main"), sort_keys=True),
        )
        check(
            "the session reading is the same read twice",
            json.dumps(session(work, store=store), sort_keys=True)
            == json.dumps(session(work, store=store), sort_keys=True),
        )
        check(
            "the replay answer is the same read twice",
            json.dumps(replay(missing, derived / "aaaa.jsonl"), sort_keys=True)
            == json.dumps(replay(missing, derived / "aaaa.jsonl"), sort_keys=True),
        )
        check(
            "and the readings are",
            json.dumps(readings(mapped), sort_keys=True)
            == json.dumps(readings(mapped), sort_keys=True),
        )

    print()
    print("every documented exit status, on the path that produces it")
    with tempfile.TemporaryDirectory() as directory:
        check(
            "a project stating no configuration is told so rather than refused",
            main(["--skills-root", directory]) == NOTHING_TO_ANSWER,
            "whoever invoked this by name is owed the answer that the project states "
            "nothing, which § 7 makes an invitation rather than silence",
        )
        check(
            "this project's own readings come back",
            main(["--skills-root", config.REPO_ROOT]) == 0,
        )
        check(
            "a root that is no repository exits one",
            main(["where", "--repo-root", directory]) == 1,
        )
        check(
            "a transcript that is not there exits one",
            main(["replay", "--missing", directory, "--transcript",
                  os.path.join(directory, "no-such.jsonl")]) == 1,
        )
        check(
            "a store that is not there exits one",
            main(["session", "--root", directory, "--store",
                  os.path.join(directory, "no-store")]) == NOTHING_IS_ASKED_ABOUT,
        )
        # ⛔ And a store whose **location** could not be derived exits two, which
        # is the split the four values exist for: a role told *nothing is being
        # asked about* reports a clean resume. Found by review on this change.
        held = {name: os.environ.pop(name, None) for name in (CONFIG_DIR, HOME)}
        try:
            check(
                "a store whose location could not be derived exits two, not one",
                main(["session", "--root", directory]) == COULD_NOT_BE_READ,
                "a store nothing could locate has not answered that there is nothing in it",
            )
        finally:
            for name, value in held.items():
                if value is not None:
                    os.environ[name] = value
        check(
            "a project that maps no restoring role is told so rather than refused",
            main(["--skills-root", str(_a_project_without_the_role(Path(directory)))])
            == NOTHING_TO_ANSWER,
            "a role nobody mapped has nothing to restore and no reading to take (§ 7)",
        )
        # ⛔ The one path the hook invokes, which no assertion reached: the
        # subcommand itself, through `main`, with the payload on standard input.
        held_in = sys.stdin
        try:
            sys.stdin = io.StringIO(json.dumps(_a_payload(**{TOKENS: 617688})))
            check("the resume subcommand answers through main", main(["resume"]) == 0)
            sys.stdin = io.StringIO("not json at all")
            check(
                "and a payload it cannot read is silence rather than a refusal",
                main(["resume"]) == 0,
                "a hook that cannot read its own event must not stand in the way",
            )
        finally:
            sys.stdin = held_in

    print()
    check(
        "this run executed assertions rather than reporting a green nothing",
        ran > 1,
        "a suite that executes no case and exits zero is the degradation every check "
        "here is written against",
    )
    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for label in failures:
            print(f"  - {label}")
        return 1
    print(f"every check passed ({ran} assertions).")
    return 0


# --- the command line ------------------------------------------------------

NOTHING_IS_ASKED_ABOUT = 1
COULD_NOT_BE_READ = 2
NOTHING_TO_ANSWER = 3


def _print(payload: dict) -> None:
    print(json.dumps(payload, indent=2, ensure_ascii=False))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="The restoring role's readings, and the evidence each is read out of.",
    )
    parser.add_argument("--skills-root", default=".")
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="what")

    where = sub.add_parser("where", help="where the work is, read-only and unfetched")
    where.add_argument("--repo-root", required=True)
    where.add_argument("--remote", default=REMOTE)
    where.add_argument("--base", default=None)

    last = sub.add_parser("session", help="what the last pass was doing")
    last.add_argument("--root", required=True)
    last.add_argument("--store", default=None)
    last.add_argument("--exclude", default="", help="a transcript this pass is itself writing")

    lost = sub.add_parser("replay", help="whether a file that is gone replays, and from what")
    lost.add_argument("--missing", required=True)
    lost.add_argument("--transcript", required=True)

    sub.add_parser("resume", help="the `SessionStart` arm, payload on stdin")

    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    # ⛔ The three readings below are procedure and are answered before any
    # configuration is read: each holds what it is handed by path, so a project
    # that configures nothing still gets an answer out of them.
    if args.what == "where":
        found = position(args.repo_root, remote=args.remote, base=args.base)
        _print(found)
        return NOTHING_IS_ASKED_ABOUT if "branch" not in found else 0

    if args.what == "session":
        found = session(args.root, store=args.store, exclude=args.exclude)
        _print(found)
        if found["found"]:
            return 0
        # ⛔ Two different answers, and collapsing them was the conflation the
        # exit statuses exist to prevent: a store that is **there and empty** is
        # nothing being asked about, while a store whose location could not be
        # derived at all is something that had to be read and could not be.
        # Found by review on this change.
        return NOTHING_IS_ASKED_ABOUT if found["store"] else COULD_NOT_BE_READ

    if args.what == "replay":
        found = replay(args.missing, args.transcript)
        _print(found)
        return NOTHING_IS_ASKED_ABOUT if "unestablished" in found else 0

    if args.what == "resume":
        try:
            payload = json.loads(sys.stdin.read() or "{}")
        except ValueError:
            # ⛔ Silence and not a refusal: a hook that cannot read its own event
            # has nothing to report and must not stand in the way of the session.
            return 0
        answered = resume_answer(payload if isinstance(payload, dict) else {})
        if answered:
            _print(answered)
        return 0

    # ⛔ Asked before the configuration is loaded and answered rather than
    # refused, per § 7: whoever invoked this by name is owed the answer that the
    # project states nothing.
    if not config.configured(args.skills_root):
        _print({
            "readings": [],
            "report": [
                "This project states no configuration, so nothing is known about its "
                "restoring role. Write `.claude/mjolnir.yaml`; the keys are stated in "
                "the configuration surface shipped with the toolkit."
            ],
        })
        return NOTHING_TO_ANSWER

    try:
        configuration = config.load(args.skills_root)
    except (config.ConfigError, OSError) as exc:
        print(exc, file=sys.stderr)
        return COULD_NOT_BE_READ

    if ROLE not in (configuration.get("carriers") or {}):
        _print({
            "readings": [],
            "report": [
                f"This project maps no `{ROLE}` role (§ 7), so there is nothing here to "
                "restore a session for and no reading to take."
            ],
        })
        return NOTHING_TO_ANSWER

    tracker = None
    try:
        import port  # noqa: PLC0415 -- asked only where an item reading is wanted

        tracker = port.load(args.skills_root)
    except Exception:  # noqa: BLE001 -- the port's absence is reported, never raised
        tracker = None
    taken = readings(configuration, tracker=tracker)
    _print({
        "readings": taken,
        "store": configuration.get("context.artifacts.carrier"),
        "report": report_for(configuration, taken),
    })
    return 0


if __name__ == "__main__":
    sys.exit(main())
