#!/usr/bin/env python3
"""The questions a project is asked, derived from the surface rather than listed.

A project adopts this toolkit by writing one file. Hand-writing it is how a board
id, a status word or a label prefix gets mistyped into something that fails much
later and somewhere else, so this module is the step that **asks** instead: it
interrogates what can be interrogated, puts a question for everything else, and
writes `.claude/mjolnir.yaml` from the answers.

⛔ **The question set is the surface's own key inventory, read at run time.** It
is not an enumeration in this module and never becomes one: `config.surface_facts`
already parses every fenced block of `../config/schema.md`, and what this module
adds is one fact per key -- whether that key is **detected**, **asked**, or
deliberately **not asked** with the reason stated. A facet the surface states and
this module places in none of the three is a **bug in this module**, and the
suite below is what says so.

⛔ **The install is a different step and this one asks nothing of it.** That split
is § What the toolkit installs into a project's own, and the reason is here: the
question set grows with the surface, and an artifact that had to wait for it would
wait on every facet added after it.

What this module owns, which none of its callers should perform again:

  * **The question set**, in the surface's own section order, each question
    carrying its key, its menu where the surface states a closed set, its
    requiredness and the condition that turns it on -- every one of those read
    off the surface rather than written here.
  * **The interrogation**, which writes nothing anywhere: the code host from git
    and the host's own client, and the tracker through the port's own vocabulary
    read. ⛔ **An interrogation that could not answer is reported as
    unestablished and the key is asked**, never filled with a guess.
  * **The write**, which is an **edit** of an existing file and a render only of
    one that is not there. A round trip through a parser takes out a project's
    own comments and its line terminator with nothing reporting the loss, so a
    configured project's file is edited key by key and read back twice -- once
    that it still loads, and once that it carries the change.
  * **The routing**, so that a value a repository may not hold reaches § 28's
    own file and never the tracked one.

⛔ **It writes nothing to the tracker and nothing to the code host.** Every call
it makes is a read; a setup step that labelled, filed or moved anything would be
adopting a project by changing it.

⚠️ **What it does not decide is an answer.** Where a value is neither detected nor
derivable, the question is put and this module waits: the carrier that invokes it
asks the person, hands the answers back, and nothing here picks a default for a
key the surface does not mark one for.

Usage:
    configure.py [--skills-root DIR]          whether this project is configured, what
                                          the interrogation sees, and how many
                                          questions stand
    configure.py questions [--answers FILE]   every question, in the surface's order
    configure.py interrogate [--code-root DIR]
                                          what the host and the tracker answer,
                                          and what could not be established
    configure.py write --answers FILE [--dry-run]
                                          the configuration, and § 28's own file
                                          where the answers carry a private value
    configure.py unmark                       take this module's own head marker out
    configure.py --self-test                  assert every answer against planted
                                          trees, then report this project's own

Exit status: 0 the answer was produced, 1 the write cannot be made and names why,
2 the surface or the configuration could not be read, 3 questions stand unanswered.
⚠️ The last is § 11's rule at a command line -- a write refused for want of an
answer is not the same thing as a write that would have been wrong.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface
from config import ConfigError  # noqa: E402

# ⛔ Imported for two things and neither is a rule: the one seam a tracker is
# reached through, and the words a vocabulary read answers with. Those words are
# the port's because every adapter answers in them, and a second spelling here
# would have this module reading an unestablished vocabulary as one it had read.
import port as tracker_port  # noqa: E402

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - environment, not logic
    sys.exit(
        "configure.py needs PyYAML to read an answers file and render a configuration.\n"
        "Install it with: python3 -m pip install pyyaml"
    )

# The exit status reserved for questions still standing, named for the reason
# `release.py` names its own: a caller comparing against a literal is comparing
# against a number, and the number is the least readable part of the contract.
UNANSWERED = 3

# --- the head marker -------------------------------------------------------
#
# ⛔ Nothing in it moves between runs -- no date, no version, no commit. A head
# line that moved every run would be the record of a pass § An artifact states
# what is true now forbids, and it would make every run a change.
#
# ⚠️ **And it says that edits are kept, which is the opposite of what the
# install's own marker says.** The two files are not the same kind of thing: an
# installed artifact is the toolkit's and is overwritten, while this one is the
# project's own and is edited key by key. A marker copied from the install would
# tell a reader their comments were about to be destroyed.

MARKER = "mjolnir-setup"

HEAD = (
    f"# {MARKER}: this project's configuration, written by the setup role",
    "# edits here are kept -- a later run changes only the keys it is asked to",
)


def _marked(text: str) -> bool:
    """Whether this text carries the head marker, read at the head alone.

    ⛔ The first two lines and nowhere else. Read anywhere in the file, a
    configuration that merely *quotes* the marker in a comment would read as
    written by this module, and so would this module's own source.
    """
    return any(f"{MARKER}:" in line for line in text.splitlines()[:2])


# --- what a key's segment is, where the project chose it -------------------
#
# ⛔ Grammar, and the one thing here that cannot be derived. The surface shows a
# collection by showing entries of it, and an entry's key is a name the project
# chose: `roots.code.app` is one project's root and `type_branch_prefix.bug` is
# one project's item type. A coverage map keyed on those paths would be keyed on
# the surface's own examples, so every project with differently-named roots would
# fall outside it.
#
# ⚠️ Each is a *decision* rather than a shape a parser could find, which is why
# the reason sits beside it: nothing on the surface distinguishes a fixed key
# from an entry's name, and a rule that guessed would read `host.landing` as a
# collection the first time a project had two landings.

COLLECTIONS = {
    "roots.code":
        "each entry's key is that code root's own name, chosen by the project "
        "(§ 1), so the question is asked once per root rather than once per name",
    "roots.code.*.command_roots":
        "each entry's key is a command root's own name, chosen by the project "
        "(§ 1), and the question is asked per entry",
    "carriers":
        "each key is one of the loop's role keys, and § 7 states that `carriers` "
        "carries no statement of its own keys -- the two the surface shows are "
        "examples, so the question is asked once per role the project maps",
    "type_branch_prefix":
        "each key is one of this project's own item types (§ 4.1), so the "
        "question is asked once per value `work_item.type.values` states",
    "work_item.code_root.roots":
        "each key is the carrier's own value and each value a root's name "
        "(§ 4.7), so the question is asked once per pair",
    "verify.identity":
        "each key is a deploy target's own name (§ 33), chosen by the project, "
        "so the question is asked once per target it judges on rather than once "
        "per name",
}

# The two leaf names that are a facet's own absence record. ⛔ Covered by the
# facet's `carrier` question rather than asked for separately: the surface's rule
# is that an absence is a stated decision, so the reason and its trigger are part
# of answering `none` and a question of their own would let a project answer the
# carrier and leave the decision unwritten.
RECORD_LEAVES = ("absent_reason", "revisit_when")

# --- how a key is answered -------------------------------------------------

DETECTED, ASKED, NOT_ASKED = "detected", "asked", "not_asked"


class Answer:
    """How one key of the surface is answered, and the prose that says so.

    ⛔ Three kinds and no fourth. A key with no entry here is a key this module
    would silently leave out of a project's configuration, which is the one
    failure the coverage arm of the suite exists to catch.
    """

    __slots__ = ("how", "detail", "by")

    def __init__(self, how: str, detail: str, by: str | None = None):
        self.how = how
        self.detail = detail
        # What performs the detection, for a `detected` answer: the name of the
        # reading in `interrogate` below, so a report can say which reading
        # failed rather than only that something did.
        self.by = by

    def __repr__(self) -> str:  # pragma: no cover -- a failure message's shape
        return f"Answer({self.how!r}, {self.detail!r})"


def detect(reading: str, detail: str) -> Answer:
    return Answer(DETECTED, detail, by=reading)


def ask(question: str) -> Answer:
    return Answer(ASKED, question)


def skip(reason: str) -> Answer:
    return Answer(NOT_ASKED, reason)


# The readings the interrogation takes, named so that a `detected` answer can
# say which one answers it and a report can name the one that failed.
GIT_REMOTE, GIT_TREE, HOST_CLIENT, TRACKER_VOCABULARY = (
    "git_remote", "git_tree", "host_client", "tracker_vocabulary",
)

# ⛔ One entry per key the surface declares, keyed on the **normalized** path --
# a collection's entry name replaced by `*` per `COLLECTIONS` above. The
# questions are this module's own content; everything about them that the
# surface already states is read from it instead: the menu, the requiredness,
# the condition, the default, and whether the facet has a real absent case.
#
# ⚠️ Three properties of asking run through the whole table, and each is this
# module's rather than any facet's:
#
#   * **Ask rather than infer where a wrong guess is quiet.** A code root that is
#     its own repository, or one nested inside another, cannot be guessed and
#     fails having done something plausible first.
#   * **The writer question is the one a person must answer.** A tracker can be
#     asked what its statuses are; nothing in any tracker records who is allowed
#     to set one (§ 4.2).
#   * **A menu, never a free-text field, wherever the surface names a shared
#     vocabulary.** The menu is read off the surface's own alternation, so a
#     value added there reaches the question without this table changing.

ANSWERED_BY: dict[str, Answer] = {
    # --- § 1. Roots --------------------------------------------------------
    "roots.code.*.path": detect(
        GIT_TREE,
        "the path from the skills root to the work tree git reports, which is `.` "
        "for the ordinary project whose configuration sits at its own root",
    ),
    "roots.code.*.host": ask(
        "Does this root live in a repository of its own, under its own host and "
        "slug? ⛔ Asked and never inferred: a root that is its own repository "
        "under another owner reads exactly like a directory of this one.",
    ),
    "roots.code.*.branch_model": ask(
        "Does this root use a branch model of its own, rather than the project's?",
    ),
    "roots.code.*.code_root_runs_nothing": ask(
        "Is there nothing to run at the top of this root -- every command "
        "belonging to a package root inside it?",
    ),
    "roots.code.*.command_roots.*.path": ask(
        "Where does this command root sit, relative to its code root?",
    ),
    "roots.code.*.command_roots.*.invoke": ask(
        "What does a command have to be run through in this command root?",
    ),

    # --- § 2. Code host ----------------------------------------------------
    "host.kind": detect(
        GIT_REMOTE, "the scheme and domain of the remote git reports for this root",
    ),
    "host.repo": detect(
        GIT_REMOTE, "the owner and name in the remote's own path",
    ),
    "host.landing.method": ask(
        "How does a change land on the integration branch here?",
    ),
    "host.landing.delete_branch": ask(
        "Who deletes the branch once a change has landed?",
    ),
    "host.landing.approval_covers": ask(
        "Does a merge approval cover one commit only, or survive a push that leaves "
        "the change's content the same?",
    ),
    "host.checks.workflow": detect(
        HOST_CLIENT,
        "the name each of the host's own workflow definitions states, read out of "
        "the definitions already in the tree",
    ),
    "host.checks.mirrors": ask(
        "Which command does this check run, such that running it here gives the "
        "same verdict the host's run gives? ⛔ Asked and not read out of the "
        "definition: nothing in this toolkit holds the facet to the command a "
        "workflow's steps run, so a value read out of one would be a reading no "
        "later check keeps true.",
    ),
    "host.checks.triggers": detect(
        HOST_CLIENT,
        "the events and branches each workflow definition states, read out of its "
        "own trigger block",
    ),
    "host.checks.command_root": ask(
        "Which command root does this check's mirrored command run in?",
    ),
    "host.checks.paths.excluding": ask(
        "Which paths under this check's own does it not run for?",
    ),
    "host.checks.jobs.mirrors": ask(
        "And which command does this job of the workflow run? ⛔ Asked for the "
        "reason the entry's own `mirrors` is: nothing here holds the facet to the "
        "command a definition's steps run, so a value read out of one would be a "
        "reading no later check keeps true.",
    ),
    "host.checks.jobs.job": detect(
        HOST_CLIENT,
        "each job's own id, read out of the same definition",
    ),
    "host.checks.jobs.command_root": ask(
        "Which command root does this job's mirrored command run in?",
    ),
    "host.checks.jobs.paths": ask(
        "Which paths does this job of the workflow run for?",
    ),
    "host.runner.label": ask(
        "What does a job have to name to reach this project's own runner?",
    ),
    "host.runner.budget_minutes": ask(
        "What is the minute budget a job here is held to?",
    ),
    "host.runner.concurrent_jobs": ask(
        "How many jobs can run at once on this runner?",
    ),
    "host.runner.supersedes": ask(
        "Which group does a newer run of this workflow supersede a running one in?",
    ),
    "host.pull_request_title.reference": ask(
        "What does a change's title open with, to name the work item it carries?",
    ),
    "host.pull_request_title.repeated": ask(
        "How does a title name more than one item?",
    ),
    "host.pull_request_title.into": ask(
        "Which base branches is that title form required for?",
    ),
    "host.runs.kind": detect(
        GIT_REMOTE,
        "the host kind above, where that host's runs are a port this toolkit "
        "implements; a host whose runs nothing here can ask about is `none`",
    ),

    # --- § 3. Tracker port -------------------------------------------------
    "tracker.kind": ask(
        "Which tracker holds this project's work items? ⛔ Asked rather than "
        "detected even where the code host is known: the same host carries plain "
        "issues and a board, and the two are different trackers.",
    ),
    "tracker.project.owner": ask(
        "Who owns the board this project's items sit on?",
    ),
    "tracker.project.number": ask(
        "Which number does that board have?",
    ),
    "tracker.site": ask(
        "Which site does this tracker live at?",
    ),
    "tracker.project_key": ask(
        "Which project key do this project's items carry?",
    ),
    "tracker.board": ask(
        "Which board do this project's items sit on?",
    ),
    "tracker.status_field.name": detect(
        TRACKER_VOCABULARY,
        "the field the tracker's own status vocabulary is read from, where this "
        "tracker carries status in a field rather than in a state",
    ),
    "tracker.status_field.resolve": ask(
        "How is that field resolved -- by its name, or by an id this project states?",
    ),
    "tracker.lists.resolve": ask(
        "How are this tracker's lists resolved -- by name, or by id?",
    ),
    "tracker.transitions.resolve": ask(
        "How is a transition resolved -- by the status it reaches, or by its own id?",
    ),
    "tracker.policy.forbid_on_item": ask(
        "Which classes of content may not be written onto an item here?",
    ),

    # --- § 4. Work-item facets ---------------------------------------------
    "work_item.type.carrier": detect(
        TRACKER_VOCABULARY,
        "whether this tracker carries a native type, a prefixed label, or "
        "neither -- which is read off the tracker rather than asked (§ 4.1)",
    ),
    "work_item.type.values": detect(
        TRACKER_VOCABULARY, "the type vocabulary the tracker itself states",
    ),
    "work_item.type.label_prefix": detect(
        TRACKER_VOCABULARY,
        "the prefix the tracker's own type labels share, where the carrier is a "
        "label",
    ),
    "type_branch_prefix.*": ask(
        "What does a branch for an item of this type start with?",
    ),
    "work_item.estimate.carrier": ask(
        "How is an estimate carried on an item here? ⛔ Asked and not detected: a "
        "tracker's custom fields do not say which of them is the estimate, and a "
        "project that estimates nothing is an ordinary configuration (§ 4.3).",
    ),
    "work_item.estimate.label_prefix": detect(
        TRACKER_VOCABULARY,
        "the prefix this tracker's estimate labels share, where the carrier is a "
        "label",
    ),
    "work_item.estimate.unit": ask(
        "Is an estimate here in points or in hours?",
    ),
    "work_item.estimate.values": detect(
        TRACKER_VOCABULARY,
        "the values the tracker's own estimate labels or field options state",
    ),
    "work_item.estimate.band": ask(
        "Above which value is an item too big to take as one piece?",
    ),
    "work_item.due_date.carrier": ask(
        "How is the date a gate writes carried on an item here?",
    ),
    "work_item.due_date.field": skip(
        "the field's name is this facet's own carrier question answered: that "
        "question offers the tracker's field list as its menu, so naming the "
        "field *is* saying the carrier is a field, and a question of its own "
        "would let a project state one without the other",
    ),
    "work_item.priority.carrier": ask(
        "How is priority carried on an item here?",
    ),
    "work_item.priority.field": skip(
        "the field's name is this facet's own carrier question answered: that "
        "question offers the tracker's field list as its menu, so naming the "
        "field *is* saying the carrier is a field, and a question of its own "
        "would let a project state one without the other",
    ),
    "work_item.priority.label_prefix": detect(
        TRACKER_VOCABULARY,
        "the prefix this tracker's priority labels share, where the carrier is a "
        "label",
    ),
    "work_item.priority.values": detect(
        TRACKER_VOCABULARY,
        "the priority vocabulary the tracker states, most takeable first",
    ),
    "work_item.priority.writer": ask(
        "Who is allowed to set an item's priority? ⛔ The writer question, which "
        "no tracker records and which is therefore a person's to answer (§ 4.2).",
    ),
    "work_item.grouping.carrier": ask(
        "How is the grouping above an item carried -- the iteration, sprint, "
        "version or milestone it belongs to?",
    ),
    "work_item.grouping.kind": ask(
        "Which of those is it: an iteration, a version, or a milestone?",
    ),
    "work_item.grouping.field": skip(
        "the field's name is this facet's own carrier question answered: that "
        "question offers the tracker's field list as its menu, so naming the "
        "field *is* saying the carrier is a field, and a question of its own "
        "would let a project state one without the other",
    ),
    "work_item.grouping.label_prefix": detect(
        TRACKER_VOCABULARY,
        "the prefix this tracker's grouping labels share, where the carrier is a "
        "label",
    ),
    "work_item.grouping.current": ask(
        "Can the current grouping be discovered from the tracker, or does this "
        "project state which one it is?",
    ),
    "work_item.grouping.has_own_acceptance": ask(
        "Does a grouping here carry an acceptance condition of its own?",
    ),
    "work_item.grouping.closes_items": ask(
        "Does closing a grouping close the items in it?",
    ),
    "work_item.grouping.closed_by": ask(
        "Who closes a grouping?",
    ),
    "work_item.grouping.ref_prefix": ask(
        "What does a ref claiming a whole grouping start with?",
    ),
    "work_item.template.carrier": ask(
        "Where does the body a new item is written to come from?",
    ),
    "work_item.template.dir": ask(
        "Which directory holds those templates?",
    ),
    "work_item.template.by_type": ask(
        "Which template does each item type use?",
    ),
    "work_item.template.sections.outcome": ask(
        "Which heading does a body state its outcome under?",
    ),
    "work_item.template.sections.acceptance": ask(
        "Which heading does a body state its acceptance check under?",
    ),
    "work_item.template.sections.reproduction": ask(
        "Which heading does a body state a reproduction under?",
    ),
    "work_item.code_root.carrier": ask(
        "How does an item say which code repository it belongs to? ⛔ Asked "
        "whatever the tracker answers: the carrier is a convention this project "
        "keeps, and a tracker with one field free reads the same either way.",
    ),
    "work_item.code_root.field": skip(
        "the field's name is this facet's own carrier question answered: that "
        "question offers the tracker's field list as its menu, so naming the "
        "field *is* saying the carrier is a field, and a question of its own "
        "would let a project state one without the other",
    ),
    "work_item.code_root.label_prefix": detect(
        TRACKER_VOCABULARY,
        "the prefix this tracker's repository labels share, where the carrier is "
        "a label",
    ),
    "work_item.code_root.roots.*": ask(
        "Which code root does this carrier value name?",
    ),

    # --- § 4.2 / § 5 / § 13 -- the lists and their entries -----------------
    "statuses": detect(
        TRACKER_VOCABULARY,
        "the state vocabulary the tracker itself states, in its own order",
    ),
    "role": ask(
        "Which role on the route does this status play? ⛔ The one list a tracker "
        "cannot be asked for: the words are the tracker's and what each of them "
        "*means* to the route is this project's (§ 4.2).",
    ),
    "writer": ask(
        "Who is allowed to move an item into this status? ⛔ The writer question "
        "again, and the reason § 4.2 gives for it: nothing in any tracker records "
        "who may set a status.",
    ),
    "readiness": ask(
        "Which of the shared predicates gate an item into committed work here? "
        "⛔ A menu off the surface's own `check` vocabulary, never a free-text "
        "field: a predicate this toolkit does not implement is one nothing runs.",
    ),
    "check": skip(
        "the predicate's own name is the readiness question's answer: that "
        "question's menu is this key's alternation, so answering it states the "
        "check",
    ),
    "on_fail": ask(
        "Does a failure of this predicate flag the item, or stop quietly? ⚠️ The "
        "second is for a predicate whose failure is not a defect -- an item that "
        "is correct and merely early has nothing for its author to fix.",
    ),
    "done.check": ask(
        "Which checks say a change here is done? ⛔ A menu off the surface's own "
        "vocabulary, for the reason the readiness list is one.",
    ),
    "done.answered_by": ask(
        "Who answers that check -- the procedure, or a person?",
    ),
    "reversals.trigger": ask(
        "Which backwards moves does this project perform, and on what?",
    ),
    "reversals.to_role": ask(
        "Which role does that move send the item back to?",
    ),
    "reversals.writer": ask(
        "Who makes that backwards move?",
    ),
    "recorded_answer.question": skip(
        "the vocabulary a recorded answer is keyed by is § 7's own closed list "
        "and no project states it: a role writes a record under one of those "
        "names, and a project that could add a name would be writing a record no "
        "guard resolves",
    ),

    # --- § 6. Commit behaviour ---------------------------------------------
    "commit.staging.session": ask(
        "Does the bookkeeping role stage what it commits explicitly, or take the "
        "whole tree?",
    ),
    "commit.staging.finish": ask(
        "And the finishing role?",
    ),
    "commit.staging.review": ask(
        "And the reviewing role?",
    ),
    "commit.trailer": ask(
        "What trailer does a commit here carry, if any?",
    ),

    # --- § 7. Carrier ------------------------------------------------------
    "carriers.*": ask(
        "Which roles of the loop does this project map, and what carries each "
        "one -- a skill, a command, or a hook? ⚠️ An absent role is a legitimate "
        "configuration rather than a partial install (§ 7).",
    ),

    # --- § 8. Language, register, audience ---------------------------------
    "language.work_item": ask(
        "Which language are this project's work items written in?",
    ),
    "language.repo": ask(
        "And the repository -- its commits, branches and change descriptions?",
    ),
    "language.prose_width": ask(
        "Which column does prose in this repository's own files wrap at?",
    ),
    "language.artifacts.day_log": ask(
        "Which language, register and audience does the day log carry?",
    ),
    # ⛔ Three keys and not one, because § 8 states three. One question covering
    # them would be the merge the surface names those roles apart to prevent: a
    # project moving one of these readers and not the others has nothing to move.
    "language.artifacts.session_summary": ask(
        "And a summary of one session, for a reader outside the build?",
    ),
    "language.artifacts.billing_report": ask(
        "And a billing period's line items, for whoever pays the invoice?",
    ),
    "language.artifacts.hours_breakdown": ask(
        "And a period's hours broken down over the work it shipped?",
    ),

    # --- § 9. Day log ------------------------------------------------------
    "day_log.day_start": ask(
        "At what hour does a working day start here? ⚠️ Marked with a default on "
        "the surface, so the question offers that and takes silence as it.",
    ),
    "day_log.round_to": ask(
        "What fraction of an hour is a day's figure rounded to?",
    ),
    "day_log.round_ties": ask(
        "And a tie -- down or up?",
    ),
    "day_log.enforce_grid": ask(
        "Must every figure sit on that grid?",
    ),
    "day_log.streams": ask(
        "Which streams is a day measured from? ⛔ A menu off the surface's own "
        "list, each member being a stream this toolkit can read.",
    ),
    "day_log.exclusions": ask(
        "Which classes of work are deducted from a day's figure? ⛔ A menu off "
        "the surface's own shared list.",
    ),
    "day_log.extra_exclusions": ask(
        "And any class of this project's own, beyond that list?",
    ),
    "day_log.ritual_retired": ask(
        "Which commands did this project used to run that no longer count as "
        "work?",
    ),
    "day_log.sections": ask(
        "Does the entry carry the billed work alone, or both halves?",
    ),
    "day_log.attribute_to": ask(
        "Whose day is this log? ⛔ Marked `# private` on the surface, so the "
        "answer is routed to § 28's own file and never written into the tracked "
        "configuration.",
    ),
    "day_log.destination.kind": ask(
        "Where is a day's entry recorded?",
    ),
    "day_log.destination.out_dir": ask(
        "Which directory does that destination write into?",
    ),
    "day_log.destination.sheet": ask(
        "Which spreadsheet holds the entries? ⛔ Marked `# private` on the "
        "surface, so the answer is routed to § 28's own file and never written "
        "into the tracked configuration.",
    ),
    "day_log.destination.tab": ask(
        "Which tab of it is an entry one row of?",
    ),
    # ⚠️ One question per role rather than one about the mapping. The surface
    # states the three roles and the project supplies a word for each, so a
    # single question would be one answer a project has to shape itself — and
    # § 26 makes the sheet's own layout the thing being read, which is three
    # separate readings off one header row.
    "day_log.destination.columns.date": ask(
        "Which header word in that tab is over the column carrying the day? "
        "⚠️ The sheet's own word, read off its header row — § 26 makes the "
        "layout the project's rather than this toolkit's.",
    ),
    "day_log.destination.columns.hours": ask(
        "And the word over the column carrying the hours?",
    ),
    "day_log.destination.columns.description": ask(
        "And the word over the column carrying the description?",
    ),
    "day_log.evidence.chat.kind": ask(
        "Is a chat archive evidence for a day here, and in which form?",
    ),
    "day_log.evidence.chat.path": ask(
        "Where is that archive? ⛔ Private, so it is routed as the attribution "
        "above is.",
    ),
    "day_log.evidence.chat.patterns": ask(
        "Which threads in it are this project's? ⛔ Private.",
    ),
    "day_log.evidence.chat.exclude": ask(
        "And which are excluded outright? ⛔ Private.",
    ),
    "day_log.evidence.chat.mixed": ask(
        "Which threads carry more than one project's work? ⛔ Private.",
    ),
    "day_log.evidence.calendars": ask(
        "Which calendars are evidence for a day here? ⛔ Private.",
    ),

    # --- § 10. Branch model ------------------------------------------------
    "branch_model.kind": ask(
        "Does work here happen in a tree of its own per item, or in place?",
    ),
    "branch_model.work_in_shared_checkout": ask(
        "May a session work in the shared checkout?",
    ),
    "branch_model.parallel_trees": ask(
        "May more than one tree stand at once?",
    ),
    "branch_model.tree_dir": ask(
        "Which directory do those trees sit under?",
    ),
    "branch_model.mechanics": ask(
        "What brings a new tree up and takes it down -- the project's own setup, "
        "named rather than described?",
    ),
    "branch_model.regenerable": ask(
        "Which ignored paths does a rebuild write again? ⚠️ A new tree carries "
        "none of them, so they are read out before any removal.",
    ),
    "branch_model.exclusive_resources.name": ask(
        "Which resource here may only be held by so many at once?",
    ),
    "branch_model.exclusive_resources.cap": ask(
        "How many may hold it?",
    ),
    "branch_model.exclusive_resources.subject": ask(
        "Is a place held by a tree, or by one call?",
    ),
    "branch_model.exclusive_resources.claimed_by": ask(
        "Which calls claim a place on it?",
    ),
    "branch_model.exclusive_resources.probe": ask(
        "Can the resource be asked how many are held? ⚠️ A resource that cannot "
        "is not a resource whose count is zero.",
    ),
    "branch_model.exclusive_resources.ttl": ask(
        "How long does a place live before it is handed back? ⚠️ A long value is "
        "the unsafe direction here, which is the opposite of how a timeout reads.",
    ),

    # --- § 11 / § 12 -------------------------------------------------------
    "ordering.carrier": ask(
        "Does this project state what is takeable next by a command of its own?",
    ),
    "ordering.command": ask(
        "Which command is it? ⚠️ Stated whole: the procedure supplies no "
        "interpreter in front of it.",
    ),

    # --- § 40. The record the ordering is kept in --------------------------
    "ordering.record.carrier": ask(
        "Where is that order *kept* — in one of this tracker's own groupings, or "
        "in a document outside every tree? ⚠️ A different question from the one "
        "above: that says how the order is read, and this says what the "
        "closing-out role edits.",
    ),
    "ordering.record.grouping": ask(
        "Which grouping? ⚠️ The grouping's own key, not which one is current.",
    ),
    "ordering.record.dir": ask(
        "Which directory does the baseline a pass measures drift against sit in — "
        "and the document with it, where the record is one? ⚠️ Outside every "
        "tree, or a teardown takes the plan for work nobody has started.",
    ),
    "ordering.record.document": ask(
        "And which document inside it?",
    ),

    # --- § 11. Session context ---------------------------------------------
    "context.artifacts.carrier": ask(
        "Where does an artifact that crosses a role boundary live?",
    ),
    "context.artifacts.dir": ask(
        "Which directory?",
    ),
    "context.artifacts.committed": ask(
        "Is it committed?",
    ),

    # --- § 14. What a role holds -------------------------------------------
    "environment.inherits": ask(
        "Which environment variables does a role here inherit? ⛔ A list of names "
        "and never a value: a variable the project has not named is either a "
        "credential to take out of the shell or a name to add here.",
    ),

    # --- § 15. End-to-end coverage -----------------------------------------
    "e2e_register.carrier": ask(
        "Is there an end-to-end register here, recording a row per scenario?",
    ),
    "e2e_register.register": ask(
        "Which file carries it?",
    ),
    "e2e_register.heading": ask(
        "Under which heading?",
    ),
    "e2e_register.suite": ask(
        "Which suite are its rows held against?",
    ),
    "e2e_register.cases": ask(
        "Which cases of that suite?",
    ),
    "e2e_register.judged": ask(
        "Which trees is a change judged over?",
    ),
    "e2e_register.exemptions": ask(
        "Which scenarios are exempt, and why each?",
    ),

    # --- § 16. What a run executed -----------------------------------------
    "executed.carrier": ask(
        "Can a run here be asked what it actually executed?",
    ),
    "executed.reports": ask(
        "Which command reports that count?",
    ),
    "executed.declares": ask(
        "And where does the tree declare what it should be?",
    ),
    "executed.min": ask(
        "Is there a floor below which a run counts as not having run?",
    ),
    "executed.requires": ask(
        "Which preconditions do those cases need that the run does not check?",
    ),

    # --- § 17. The local verdict -------------------------------------------
    "checks_local.command": ask(
        "Which command produces a verdict here that no run of the host mirrors?",
    ),
    "checks_local.proves": ask(
        "What does this local check's verdict prove?",
    ),
    "checks_local.command_root": ask(
        "Which command root does it run in?",
    ),
    "checks_local.counts_when": ask(
        "Under which conditions does its verdict count?",
    ),
    "checks_local.invalidate": ask(
        "What invalidates it -- which cached pass must not read as work done?",
    ),
    "checks_local.requires": ask(
        "Which preconditions does it need that it does not check itself?",
    ),

    # --- § 18. The guard on a command already run --------------------------
    "already_run.never_guard": ask(
        "Which commands does that guard never refuse, whatever the host has run?",
    ),
    "already_run.operational_when": ask(
        "Under which conditions is a re-run operational rather than wasted?",
    ),
    "already_run.escape": ask(
        "Which variable lets a person run one anyway?",
    ),

    # --- § 19. A command that spends ---------------------------------------
    "spend_guard.deny.command": ask(
        "Which commands here spend money?",
    ),
    "spend_guard.deny.args_match": ask(
        "Which commands here spend money, matched on their own arguments?",
    ),
    "spend_guard.deny.reason": ask(
        "What does each one spend, said so that the refusal can name it?",
    ),
    "spend_guard.approval": ask(
        "Is a spend approved per invocation, or denied outright?",
    ),
    "spend_guard.resume_bar_usd": ask(
        "Above which figure does a resumed run stop to ask again?",
    ),

    # --- § 20. The sections a body must carry ------------------------------
    "body_sections.heading": ask(
        "Which section must a change's body carry, beyond the shared three?",
    ),
    "body_sections.when": ask(
        "Is it required before the change opens, or after?",
    ),
    "body_sections.answered_by": ask(
        "Who answers it -- the procedure, or a person?",
    ),
    "body_sections.read_by": ask(
        "Who reads it?",
    ),
    "body_sections.nothing_needed": ask(
        "What does it say where there is nothing to say?",
    ),

    # --- § 21. A command that could open a live session --------------------
    "live_guard.session_tools.command": ask(
        "Which commands here could open a session on a machine that is not this "
        "one?",
    ),
    "live_guard.session_tools.valued_flags": ask(
        "Which flags of that command take their value as a separate word?",
    ),
    "live_guard.local_names": ask(
        "Which names are reached without leaving this machine?",
    ),
    "live_guard.allowlist": ask(
        "Which machines may a session be opened on?",
    ),

    # --- § 22. What enters the window --------------------------------------
    "context_guard.unbounded.command": ask(
        "Which commands here produce output nothing bounds?",
    ),
    "context_guard.never_bound.command": ask(
        "And which must never be bounded, their whole output being the answer?",
    ),
    "context_guard.unbounded.args_match": ask(
        "Which commands here produce output nothing bounds?",
    ),
    "context_guard.unbounded.bound": ask(
        "What bounds each one?",
    ),
    "context_guard.unbounded.instead": ask(
        "What is run in its place?",
    ),
    "context_guard.unbounded.reason": ask(
        "Why, said so that the rewrite can name it?",
    ),
    "context_guard.never_bound.args_match": ask(
        "And which commands must never be bounded, their whole output being the "
        "answer?",
    ),
    "context_guard.reread": ask(
        "Is a second read of one file in a session refused, or allowed?",
    ),
    "context_guard.result_limit_chars": ask(
        "Above how many characters is a result replaced by a path and a head?",
    ),
    "context_guard.sidecar_dir": ask(
        "Which directory holds what a bounded result was written to?",
    ),

    # --- § 23 / § 24 / § 25 -- the session's own facets --------------------
    "session.parts": ask(
        "Which thirds does the bookkeeping role run here? ⛔ A menu off the "
        "surface's own list.",
    ),
    "memory.carrier": ask(
        "Where does this session's memory store live -- a path this project "
        "states, the harness's own, or nowhere?",
    ),
    "memory.store": ask(
        "Which directory holds it?",
    ),
    "memory.index": ask(
        "And which file indexes it?",
    ),
    "memory.write_from": ask(
        "May a save standing in a work tree refresh it, or the shared checkout "
        "alone?",
    ),

    # --- § 26's destination is asked with § 9's log; § 27 ------------------
    "people.carrier": ask(
        "Does this project map a role to the person who holds it? ⛔ Asked and "
        "never resolved from whoever is running: a map answered that way is an "
        "assignee the gate is configured to reject (§ 27).",
    ),
    "people.source": ask(
        "Which file carries that map?",
    ),
    "people.key": ask(
        "How does an item name a person -- a handle, a field, or a label?",
    ),
    "people.field": ask(
        "Which field?",
    ),
    "people.label_prefix": ask(
        "Which prefix do those labels share?",
    ),

    # --- § 28. A value a repository may not hold ---------------------------
    "private.carrier": detect(
        GIT_TREE,
        "whether any answer handed back sits at a key the surface marks "
        "`# private`: a project with one has a private layer and a project with "
        "none states `none`, which is the carrier rather than a question",
    ),
    "private.source": ask(
        "Which file outside this repository holds those values?",
    ),
    "private.keys": detect(
        GIT_TREE,
        "the private-marked keys the answers actually carry a value for, which is "
        "what makes the list a statement of this project rather than of the "
        "surface",
    ),

    # --- § 29's runs are asked with § 2's host; § 30 -----------------------
    "loop_exempt.classes.name": ask(
        "What is this class of change called?",
    ),
    "loop_exempt.classes.kinds": ask(
        "Which classes of change here do not go through the loop? ⛔ A menu off "
        "the surface's own list.",
    ),
    "loop_exempt.classes.paths": ask(
        "Which paths does each class reach?",
    ),
    "loop_exempt.borderline": ask(
        "A change that could be in one of those classes and could not -- is that "
        "asked, or decided by the session?",
    ),
    "loop_exempt.destination": ask(
        "Where does an exempt change land?",
    ),

    # --- § 31. Test tiers --------------------------------------------------
    "test_tiers.carrier": ask(
        "Does this project state its test tiers?",
    ),
    "test_tiers.tier": skip(
        "the tier's own name is the carrier question's answer: its alternation is "
        "that question's menu, so each tier is stated by choosing one",
    ),
    "test_tiers.needs": skip(
        "the vocabulary a tier's needs are drawn from is the surface's own list, "
        "offered as the menu of the per-tier question below rather than asked for "
        "itself",
    ),
    "test_tiers.started": skip(
        "the vocabulary is the per-tier question's menu, as the needs list is",
    ),
    "test_tiers.stood_up_by": skip(
        "the vocabulary is the per-tier question's menu, as the needs list is",
    ),
    "test_tiers.tiers.tier": ask(
        "Which tier is this -- unit, integration, end-to-end, or acceptance?",
    ),
    "test_tiers.tiers.needs": ask(
        "What does this tier need stood up before it can run at all?",
    ),
    "test_tiers.tiers.started": ask(
        "Is it started automatically, or asked for?",
    ),
    "test_tiers.tiers.stood_up_by": ask(
        "Who stands that dependency up -- the run, or the host?",
    ),
    "test_tiers.tiers.selects": ask(
        "Which cases does this tier select?",
    ),
    "test_tiers.tiers.selection_held_by": ask(
        "What holds that selection to what it claims?",
    ),
    "test_tiers.tiers.command": ask(
        "Which command runs it?",
    ),
    "test_tiers.tiers.workflow": ask(
        "Which of the host's workflows runs it?",
    ),
    "test_tiers.tiers.refused_on": ask(
        "Which targets is this tier never run against?",
    ),

    # --- § 33. Deploy targets ----------------------------------------------
    "deploy.name": ask(
        "Which deploy targets does this project have?",
    ),
    "deploy.invoke": ask(
        "How is this target reached -- a command, a dispatch, or by hand?",
    ),
    "deploy.command": ask(
        "Which command?",
    ),
    # ⛔ Asked rather than inferred, and the quiet wrong guess is the measured
    # one: the deploying role resolves this entry's command first, a command
    # root is stated per repository, so a target naming the wrong one of two
    # resolves a command in a repository its act never reaches (§ 33).
    "deploy.code_root": ask(
        "Which of this project's repositories is this target's act performed in?",
    ),
    "deploy.command_root": ask(
        "Which command root does it run in?",
    ),
    "deploy.workflow": ask(
        "Which workflow is dispatched?",
    ),
    "deploy.ref": ask(
        "Which ref does the dispatch carry?",
    ),
    "deploy.inputs": ask(
        "Which inputs?",
    ),
    "deploy.requires": ask(
        "Which preconditions does it need that it does not check itself?",
    ),
    "deploy.requires_role": ask(
        "Which role must an item already stand in to go out on this target?",
    ),
    "deploy.advances": ask(
        "Which role does a deploy move its items to?",
    ),
    "deploy.publishes": ask(
        "Does reaching this target publish what it carries? ⛔ The question a "
        "wrong guess is quiet about: a live target answered as not live is a "
        "publish nobody was asked about (§ 33).",
    ),
    "deploy.not_live": ask(
        "And where it is not live, what says so?",
    ),
    "deploy.batch": ask(
        "Which command narrows the batch this target carries?",
    ),
    "deploy.grouping": ask(
        "Which grouping does a release on this target mark?",
    ),

    # --- § 34. The files that carry a version ------------------------------
    "release.carrier": ask(
        "Does any file here carry a version a release writes?",
    ),
    "release.files.path": ask(
        "Which file?",
    ),
    "release.files.kind": ask(
        "Is it a pattern to replace, or a changelog to insert an entry into?",
    ),
    "release.files.pattern": ask(
        "Which pattern matches the version in it?",
    ),
    "release.files.replace": ask(
        "What replaces it?",
    ),
    "release.files.optional": ask(
        "Is the file allowed to be missing?",
    ),
    "release.changelog_ci_owned": ask(
        "Does CI own the changelog here?",
    ),
    "release.publishes_packages": ask(
        "Does cutting a release publish a package? ⛔ Asked because a version "
        "spent on a registry is spent for ever, and the go is the person's.",
    ),

    # --- § 35. The live data step a deploy performs ------------------------
    "deploy.live_data_step.backup.run": ask(
        "Which command dumps this target's live store?",
    ),
    "deploy.live_data_step.backup.verify": ask(
        "And which command reads that dump back? ⛔ Asked as a key of its own "
        "because a dump nothing read is a backup on the strength of an exit "
        "status alone, which is the measured failure (§ 35).",
    ),
    "deploy.live_data_step.rehearse": ask(
        "Does the write have a dry variant? ⚠️ An omitted one is reported as no "
        "rehearsal rather than as a clean one, so it is asked rather than left "
        "to the apply command's own flags.",
    ),
    "deploy.live_data_step.apply": ask(
        "Which command writes to the live store?",
    ),
    "deploy.live_data_step.apply_by": ask(
        "Who performs that write -- the procedure, or a person? ⛔ The project's "
        "own ruling about an act that cannot be undone, never inferred from the "
        "command's shape.",
    ),
    "deploy.live_data_step.order": ask(
        "Does the write happen before this target is invoked, or after it?",
    ),
    "deploy.live_data_step.record": ask(
        "Which command prints what has already been applied to this store, one "
        "path per line?",
    ),

    # --- § 37. The projects a billing period is assembled from -------------
    "billing.carrier": ask(
        "Is anybody invoiced for a period of hours assembled here? ⚠️ Asked "
        "apart from the day log above, which measures and records the hours: a "
        "project can record every day and bill nobody (§ 37).",
    ),
    "billing.projects": ask(
        "Which projects is a period assembled from -- the skills root of each, "
        "written absolutely? ⛔ Stated whole, this project's own root included "
        "where its hours are billed: § 37 implies nothing, and a root left out "
        "is hours nobody is charged for.",
    ),
    "billing.rates": ask(
        "And the rate per client? ⛔ Marked `# private` on the surface, so the "
        "question routes the value to § 28's untracked file and the tracked "
        "configuration states only that the key is answered there -- a rate and "
        "a client's name being the two values this toolkit holds nowhere.",
    ),

    # --- § 38. The documents a project holds to a checkable property --------
    "documents.carrier": ask(
        "Are this project's prose documents held to anything a machine can "
        "check? ⚠️ Answering no is a configuration rather than a gap: there is "
        "then no graph, and a reader asked what holds a document says nothing "
        "is stated rather than that the documents agree (§ 38).",
    ),
    "documents.files": ask(
        "Which files are the governed set, as globs from the code root? ⛔ A "
        "tracked file one of them matches and no row declares is a stop rather "
        "than a skip, so the globs are what decides how much new prose has to "
        "be placed deliberately. ⚠️ `*` stops at a separator here and `**` "
        "crosses one (§ 38).",
    ),
    "documents.entry_points": ask(
        "And which of them does a reader -- or a mechanism -- arrive at without "
        "any document naming it? ⛔ A list rather than one root, because a "
        "carrier a harness loads by name is named by no document; every other "
        "governed file has to be reachable from one of these (§ 38).",
    ),
    "documents.graph.document": ask(
        "One row per governed document: which document is this row about? ⛔ "
        "Every governed file needs one, and a document with no row sits outside "
        "the graph and is held by nothing (§ 38).",
    ),
    "documents.graph.named_as": ask(
        "And how does prose here name it -- by its path, or by something else? "
        "⚠️ Asked because the commonest answer is *something else*: a project "
        "that refers to its role carriers by slug has every edge in its graph "
        "read as dropped until it says so. Omit the key where the path is what "
        "gets written (§ 38).",
    ),
    "documents.graph.may_name": ask(
        "Which documents may this one's text name? ⛔ Held in **both** "
        "directions -- it may name only these and must name all of them -- and "
        "the three answers are different: a list, `[]` for a document that may "
        "name no other at all, and `null` for an edge this project does not "
        "enforce here (§ 38).",
    ),
    "documents.graph.derived_from": ask(
        "And which documents did its content flow in from? ⚠️ Recorded rather "
        "than enforced: this edge obliges no citation and is never compared with "
        "the text. What is held is that the record is complete and stays "
        "acyclic (§ 38).",
    ),
    "documents.forbidden.pattern": ask(
        "Which name or pattern may appear in none of them -- a module this "
        "project deleted, a word its own rules ban? ⚠️ Each entry states what "
        "keeps the forbidden thing stable, since a forbidding check is sound "
        "exactly there and nowhere else (§ 38).",
    ),
    "documents.forbidden.reason": ask(
        "What would its appearance mean? ⛔ Stated, because a refusal whose "
        "reason nobody wrote down is one nobody can tell a false refusal from "
        "(§ 38).",
    ),
    "documents.forbidden.stable_because": ask(
        "And what keeps that thing from being reworded into something else? ⛔ "
        "This is the whole soundness condition of the forbidding kind: a name "
        "that was renamed rather than removed still refers to something, and "
        "the check then refuses correct prose (§ 38).",
    ),
    "documents.quoted.sentence": ask(
        "Is any sentence quoted back at the document it came from? ⛔ This is "
        "the kind that does not work and it is admitted with a warning rather "
        "than refused: it goes red on an innocent reword and green when the "
        "claim is reworded into its opposite, so its green says nothing about "
        "the claim. Derive the property instead, where you can (§ 38).",
    ),
    "documents.quoted.document": ask(
        "And which document is it quoted against? ⛔ One the graph declares: a "
        "sentence quoted at a document outside the governed set is a check over "
        "a file nothing else here reads (§ 38).",
    ),

    # --- § 39. The specification corpus, and which copy of it governs -------
    "spec_corpus.carrier": ask(
        "Is this project's specification a tree in this repository, with a copy "
        "per version on each version's own branch? ⚠️ Answering no is a "
        "configuration rather than a gap, and a specification kept in a wiki or "
        "a document store is that no: it would be a port rather than a ref "
        "read. ⛔ The filing role then files normally and says that no corpus is "
        "configured — never that nothing contradicts the request (§ 39).",
    ),
    "spec_corpus.files": ask(
        "Which files are the corpus, as globs from the code root? ⚠️ `*` stops "
        "at a separator here and `**` crosses one, the same semantics the "
        "governed set above carries. ⛔ There is no root key: one would make "
        "every glob relative to a second thing, and the two spellings of a path "
        "would be free to disagree (§ 39).",
    ),
    "spec_corpus.load_bearing": ask(
        "And which of them are read **whole**? ⛔ The rest is matched on "
        "keywords from the request, so this is the part a reading may not miss. "
        "⚠️ `[]` is a real answer and means every document is reached by "
        "keyword — unlike the corpus itself, which may not be empty (§ 39).",
    ),
    "spec_corpus.grouping": ask(
        "Which of this project's groupings names the ref the corpus is read at? "
        "⛔ Asked only where several are carried: the one above resolves to a "
        "single entry, and the ref is that grouping's `ref_prefix` joined onto "
        "the value the item carries — no second key states a branch-naming "
        "scheme (§ 39, § 4.8).",
    ),

    # --- § 41. What a deployed item is judged against ----------------------
    "verify.carrier": ask(
        "Does anybody judge a deployed item against its own criteria here? ⚠️ "
        "Asked apart from the deploy above: a project can deploy every day and "
        "judge nothing through the procedure, and ⛔ a ladder with no accepted "
        "state in it has nowhere for a verdict to go (§ 41).",
    ),
    "verify.identity.*": ask(
        "For this target, which command prints the commit it serves? ⛔ Read off "
        "a file inside the running target -- never an artefact digest, which a "
        "reproducible build makes identical from another commit, and never the "
        "integration branch, which runs ahead of every target (§ 41).",
    ),
    "verify.baseline.ref": ask(
        "Which ref does the comparison call `before`?",
    ),
    "verify.baseline.harness": ask(
        "And which path are both sides built under? ⛔ A durable one: a "
        "comparison whose two sides are gone cannot be re-read when somebody "
        "disputes it, and the dispute is the only reason it was built (§ 41).",
    ),
    "verify.breakpoints": ask(
        "Which widths may a handover name? ⛔ Widths and never device-class "
        "names -- a name reads like one and is not one. `[]` is the answer for a "
        "project whose handover says nothing about geometry (§ 41).",
    ),
}


# --- the key inventory, derived ---------------------------------------------


def normalized(path: str) -> str:
    """One declared path with each project-chosen segment replaced by `*`.

    ⛔ Applied to the path's own *prefix* at each segment rather than to the
    whole: `roots.code.app.command_roots.api-service.path` has two chosen names
    at different depths, and a pattern matched against the full path could only
    reach the outermost.
    """
    out: list[str] = []
    for segment in path.split("."):
        prefix = ".".join(out)
        out.append(
            "*" if any(fnmatch.fnmatch(prefix, known) for known in COLLECTIONS)
            else segment
        )
    return ".".join(out)


# A list entry's own opening key, which the reader beside this module
# deliberately does not yield: `_walk_keys` skips a `- ` line because an entry is
# not a key. ⛔ Read here rather than there, and that is a **new** reading rather
# than a second copy of one -- the reader's rule is about what a *project* must
# write, and these keys are written once per entry rather than once per file.
#
# ⚠️ Measured, which is why it is here at all: nine keys of the surface are
# written this way -- `host.checks.workflow` and `test_tiers.tiers.tier` among
# them -- and every one of them was invisible to a coverage walk taken off
# `declared` alone. A question set that missed them would be a question set a
# project could answer in full and still have an unwritable configuration.
ENTRY_LINE = re.compile(r"^(?P<indent>\s*)-\s+(?P<key>[A-Za-z_][\w-]*):")
KEY_LINE = re.compile(r"^(?P<indent>\s*)(?P<key>[A-Za-z_][\w-]*):")


def walk(surface_text: str):
    """Yield `(the normalized path, the section it is stated under)` in file order.

    The walk is the reader's own -- indentation is the nesting -- and the one
    difference is which lines yield a path: a `- key:` line names the first key
    of an entry of whatever list it sits in, so its path is the enclosing keys
    plus its own, and a plain `key:` line yields its own path as the reader
    already reads it.

    ⛔ **One pass over both shapes**, rather than two walks joined afterwards.
    Document order is what the question set is put in, and two walks concatenated
    would put every entry's opening key after every other question -- so a
    project would be asked which command a check mirrors before being asked
    whether it has any checks at all.
    """
    for heading, block in config._fences(surface_text):
        stack: list[tuple[int, str]] = []
        for line in block.splitlines():
            entry = ENTRY_LINE.match(line)
            if entry:
                indent = len(entry.group("indent"))
                while stack and stack[-1][0] >= indent:
                    stack.pop()
                path = ".".join([key for _, key in stack] + [entry.group("key")])
                yield normalized(path), heading
                continue
            key = KEY_LINE.match(line)
            if key:
                indent = len(key.group("indent"))
                while stack and stack[-1][0] >= indent:
                    stack.pop()
                stack.append((indent, key.group("key")))
                yield normalized(".".join(name for _, name in stack)), heading


def entry_keys(surface_text: str) -> dict[str, str]:
    """`the entry's opening key path -> the section it is stated under`."""
    found: dict[str, str] = {}
    for heading, block in config._fences(surface_text):
        stack: list[tuple[int, str]] = []
        for line in block.splitlines():
            entry = ENTRY_LINE.match(line)
            if entry:
                indent = len(entry.group("indent"))
                while stack and stack[-1][0] >= indent:
                    stack.pop()
                path = ".".join([key for _, key in stack] + [entry.group("key")])
                found.setdefault(normalized(path), heading)
                continue
            key = KEY_LINE.match(line)
            if key:
                indent = len(key.group("indent"))
                while stack and stack[-1][0] >= indent:
                    stack.pop()
                stack.append((indent, key.group("key")))
    return found


# A top-level key of a configuration: a `key:` line at the very start of a
# fenced line. ⛔ The **unindented** ones alone, and that is not a shortcut. The
# surface shows several facets in a fence that opens at an indent -- § 4.1's
# branch prefixes, § 4.2's status fields, § 5's predicate -- so a walk reading
# those as top-level keys would ask a project for a `check:` block at the head of
# its file, which no configuration has and the reader refuses.
#
# ⚠️ The same derivation the single-source gate takes over the configurations it
# holds, so the set this module writes and the set that gate requires are read
# off one statement rather than two.
TOP_LEVEL = re.compile(r"^(?P<key>[a-z_][a-z0-9_]*):")


def blocks(surface_text: str) -> list[str]:
    """Every top-level key a configuration carries, in the surface's own order."""
    seen: list[str] = []
    for _heading, block in config._fences(surface_text):
        for line in block.splitlines():
            found = TOP_LEVEL.match(line)
            if found and found.group("key") not in seen:
                seen.append(found.group("key"))
    return seen


def inventory(surface_text: str) -> dict[str, str]:
    """Every key the surface declares that a project writes a value for.

    ⛔ Derived whole, and the two things taken out of it are rules rather than a
    list: a path with declared children is a **block** and carries no value of
    its own, and a facet's own absence record is covered by its `carrier`
    question. ⚠️ `the normalized path -> the section it is stated under`, so a
    question can cite the section the key is stated in without this module
    carrying a section list.
    """
    sections: dict[str, str] = {}
    for path, heading in walk(surface_text):
        sections.setdefault(path, heading)
    children = {path.rsplit(".", 1)[0] for path in sections if "." in path}
    return {
        path: heading
        for path, heading in sections.items()
        if path not in children and path.rsplit(".", 1)[-1] not in RECORD_LEAVES
    }


def coverage(surface_text: str) -> list[str]:
    """What this module's table and the surface disagree about.

    ⛔ Both directions, and the second is not decoration: a key the table names
    and the surface no longer declares is a question about a facet that is gone,
    and the project it is put to answers it into a configuration the reader
    refuses. Measured while this module was being written -- one such entry,
    carrying a question nobody could act on.
    """
    declared = inventory(surface_text)
    problems = []
    for path in sorted(set(declared) - set(ANSWERED_BY)):
        problems.append(
            f"{path}: the surface declares it under § {declared[path]} and this "
            "module places it in none of detected, asked or deliberately not "
            "asked. A facet the surface states and `setup` never reaches is a bug "
            "here rather than a facet a project hand-writes."
        )
    for path in sorted(set(ANSWERED_BY) - set(declared)):
        problems.append(
            f"{path}: this module answers it and the surface declares no such "
            "key. A question about a facet that is gone is one a project cannot "
            "answer into a configuration the reader accepts."
        )
    return problems


# --- the question set -------------------------------------------------------


def _at(data, path: str):
    """The value a nested answers block states at a dotted path, or `None`.

    ⚠️ A collection's `*` matches whatever key the project chose, so a path
    through one answers *whether any entry states it* rather than which: the
    question is asked per entry and what this reports is whether the entry's
    question has been reached at all.
    """
    if not isinstance(data, dict):
        return None
    head, _, rest = path.partition(".")
    if head == "*":
        for value in data.values():
            found = _at(value, rest) if rest else value
            if found is not None:
                return found
        return None
    if isinstance(data, list):  # pragma: no cover -- guarded by the caller
        return None
    found = data.get(head)
    if not rest:
        return found
    if isinstance(found, list):
        for member in found:
            reached = _at(member, rest)
            if reached is not None:
                return reached
        return None
    return _at(found, rest)


def questions(
    surface_text: str,
    answers: dict | None = None,
    detected: dict | None = None,
    menus: dict | None = None,
) -> list[dict]:
    """Every question this project is asked, in the surface's own order.

    Each carries what the surface states about the key and nothing this module
    decided: the menu where the surface states a closed set, the default where it
    marks one, whether the key is required and under which condition, and whether
    its value is one a repository may not hold.

    ⛔ A question whose key the interrogation answered is **dropped** rather than
    put with a suggestion, and a question whose key an answers block already
    carries is dropped too: *detect what is detectable, ask the rest* is the rule,
    and a run that re-asked what it had just read would be asking a person to
    confirm a reading they have no way to check.
    """
    facts = config.surface_facts(surface_text)
    declared = inventory(surface_text)
    detected = detected or {}
    menus = menus or {}
    out = []
    for path in _in_surface_order(surface_text, declared):
        answer = ANSWERED_BY[path]
        if answer.how == NOT_ASKED:
            continue
        if answer.how == DETECTED and path in detected:
            continue
        if answers is not None and _at(answers, path) is not None:
            continue
        # ⛔ **A key a configured project left unset has been answered**, and the
        # answer is that it states none. The surface's own rule -- a key carrying
        # neither requiredness marker is legitimately unset -- so a re-run that
        # put the question again would ask a project to re-decide every optional
        # key in the file it already wrote. ⚠️ Read off the block the key sits in
        # rather than off the key: a project that wrote `day_log:` and no
        # `extra_exclusions` has addressed that facet, while one that wrote no
        # `host.runner` at all has not been asked about a runner yet.
        if answers is not None and not _owed(facts, answers, path):
            parent = path.rpartition(".")[0]
            if parent and _at(answers, parent) is not None:
                continue
        condition = sorted(
            f"{on} = {value}"
            for (key, on, value) in facts["required_when"]
            if normalized(key) == path
        )
        out.append({
            "key": path,
            "section": declared[path],
            "question": (
                answer.detail if answer.how == ASKED
                else f"{answer.detail} -- which could not be read, so it is asked"
            ),
            "detected_by": answer.by,
            # ⛔ The tracker's own vocabulary wins over the surface's where both
            # answer, and it is the **menu** rather than the value: a project's
            # status words are its tracker's, so a question offering this
            # surface's alternation there would offer a vocabulary no tracker
            # holds. ⚠️ The surface's own set is what a key the tracker publishes
            # nothing for still gets, which is every key that is about the
            # procedure rather than about a tracker.
            "menu": (
                menus.get(path)
                or facts["enums"].get(path)
                or facts["lists"].get(path)
                or None
            ),
            "menu_from": (
                "the tracker" if menus.get(path)
                else "the surface" if path in facts["enums"] or path in facts["lists"]
                else None
            ),
            "default": facts["defaults"].get(path, None),
            "has_default": path in facts["defaults"],
            "required": path in {normalized(k) for k in facts["required"]},
            "required_when": condition,
            "private": path in {normalized(k) for k in facts["private"]},
            "absent_case": _absent_facet(facts, path),
        })
    return out


def _owed(facts: dict, answers: dict, path: str) -> bool:
    """Whether the surface requires this key of *these* answers.

    ⛔ Both markers, and the condition read against what the answers state: a key
    required only under another key's value is owed exactly where that value is
    the one they carry.
    """
    if path in {normalized(key) for key in facts["required"]}:
        return True
    return any(
        normalized(key) == path and str(_at(answers, on)) == value
        for (key, on, value) in facts["required_when"]
    )


def _absent_facet(facts: dict, path: str) -> str | None:
    """The facet this key's `carrier` governs, where the facet may be absent.

    ⛔ Read off the surface's own `# absent_reason` mark rather than listed: a
    `carrier` question whose facet has a real absent case has to carry the
    reason and its trigger with the answer, and a facet marked after this module
    was written gets that without an edit here.
    """
    if not path.endswith(".carrier"):
        return None
    facet = path[: -len(".carrier")]
    return facet if facet in {normalized(k) for k in facts["absent_reason"]} else None


def _in_surface_order(surface_text: str, declared: dict) -> list[str]:
    """The declared keys in the order the surface states them.

    ⚠️ The order is the reader's experience of the file and is not a rule: a
    question set in dictionary order would walk `already_run` before `roots`,
    which asks a project about a guard before it has said where its code is.
    """
    seen: list[str] = []
    for path, _heading in walk(surface_text):
        if path in declared and path not in seen:
            seen.append(path)
    return seen


# --- the interrogation ------------------------------------------------------
#
# ⛔ Every reading here is a **read**. A setup step that labelled, filed or moved
# anything would be adopting a project by changing it, and the one act this step
# performs on a tree is writing the configuration it was asked for.
#
# ⛔ And a reading that did not answer is reported as unestablished with the
# reason, never as the thing it was looking for being absent -- § 2's rule that
# absence of signal is not an answer, arriving where a quiet guess would be
# cheapest. A reading that failed turns into a question.

READ = tracker_port.VOCABULARY_READ
NONE_STATED = tracker_port.VOCABULARY_NONE
UNESTABLISHED = tracker_port.VOCABULARY_UNESTABLISHED

# The port operation a tracker's own vocabularies are read through. ⛔ The name
# is § 3's and the row there states what it answers and what its absence does;
# this is the string an adapter registers it under, exactly as every other
# operation's name is a string at its registration.
READ_VOCABULARY = "read_vocabulary"

# The word every absent-capable facet's `carrier` states for its absent case.
# ⛔ One spelling, and the suite holds it against **every** such facet's own
# alternation on the surface: a second word here would make this module ask for a
# reason on the facets it happened to know about and accept a bare `none` on the
# rest.
ABSENT = "none"

# Which of the tracker's own vocabularies answers which question. ⛔ This
# module's own content and not the port's: an adapter publishes what its tracker
# states, and which key that answers is a question about *this* surface. ⚠️ A
# vocabulary an adapter does not publish leaves its keys asked, which is the
# fallback § 3 states for the operation rather than a hole here.
VOCABULARY_FOR = {
    "statuses": "statuses",
    "work_item.type.carrier": "types",
    "work_item.type.values": "types",
    "work_item.type.label_prefix": "labels",
    "work_item.estimate.label_prefix": "labels",
    "work_item.estimate.values": "labels",
    "work_item.priority.label_prefix": "labels",
    "work_item.priority.values": "labels",
    "work_item.grouping.label_prefix": "labels",
    "work_item.code_root.label_prefix": "labels",
    "tracker.status_field.name": "status_fields",
}


def _reading(answer: str, values=None, because: str = "") -> dict:
    return {"answer": answer, "values": values, "because": because}


def _git(root: str, *args: str) -> str | None:
    """What git says, or `None` where it could not be asked.

    ⛔ `None` for every failure rather than an exception, and the caller turns it
    into an unestablished reading with the key named: a project whose code root
    is not a repository yet is an ordinary thing to run this step in, and a
    traceback there would read as the step being broken.
    """
    try:
        done = subprocess.run(
            ["git", "-C", root, *args],
            capture_output=True, text=True, timeout=30, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() or None


# What a remote's path leaves once the host's own decoration is off it. ⛔ Both
# shapes a host publishes, and nothing beyond them: a remote this does not match
# is reported unestablished and the slug is asked, which is the direction a wrong
# guess cannot survive -- a mistyped slug addresses somebody else's repository
# and every call after it is about that one.
REMOTE = re.compile(
    r"^(?:(?:https?|ssh|git)://(?:[^@/]+@)?(?P<domain>[^/:]+)(?::\d+)?/"
    r"|(?:[^@]+@)?(?P<host>[^:/]+):)(?P<path>.+?)(?:\.git)?/?$"
)


def _slug(remote: str) -> tuple[str | None, str | None]:
    """`(the host's domain, the owner and name)` from one remote, or `(None, None)`."""
    found = REMOTE.match(remote)
    if not found:
        return None, None
    domain = found.group("domain") or found.group("host")
    return domain, found.group("path")


def _kind_from(domain: str) -> str:
    """The host kind a domain names.

    ⛔ The domain's own label and never a table of hosts: § 2 states no
    alternation for `host.kind`, so a list here would be this module deciding
    which hosts exist. What comes back is what the remote says, and the question
    set offers it as the detected value for a person to see rather than as a fact
    nothing can check.
    """
    label = domain.split(":")[0].rsplit(".", 2)
    return label[-2] if len(label) > 1 else domain


def interrogate(skills_root: str, answers: dict | None = None) -> dict:
    """What the host and the tracker answer, and what could not be established.

    ⛔ Two phases rather than one, and the order is the rule: the code host can
    be read from a tree alone, while a tracker cannot be reached until the keys
    that **address** it have been answered. A single-phase interrogation would
    report every tracker vocabulary unestablished on a project that had simply
    not been asked yet.
    """
    answers = answers or {}
    detected: dict[str, object] = {}
    # ⛔ A menu is not a detected value, and the two are kept apart. A tracker
    # publishes a **candidate set** -- its status words, its labels, its types --
    # and which members of it this project means is the question, so a vocabulary
    # folded into `detected` would drop the question and write the tracker's whole
    # label list as this project's answer.
    menus: dict[str, list] = {}
    report: list[dict] = []

    code_root = os.path.abspath(skills_root)
    top = _git(code_root, "rev-parse", "--show-toplevel")
    if top is None:
        report.append({
            "reading": GIT_TREE,
            "answer": UNESTABLISHED,
            "because":
                f"{code_root} is not inside a git work tree, so where this "
                "project's code sits cannot be read and is asked. ⛔ Not read as "
                "`.`: a root guessed here is the root every later call addresses.",
        })
    else:
        # ⛔ Both sides resolved before they are compared, which is not tidiness:
        # git answers with the path symlinks resolve to, while a skills root
        # handed in keeps whatever the caller wrote -- and on a system whose
        # temporary directory is a symlink the two differ for the **same**
        # directory. Measured: the relative path came back as six `..` segments
        # and an absolute tail, which would have been written into a project's
        # own `roots.code` as the path every later call addresses.
        relative = os.path.relpath(
            os.path.realpath(top), os.path.realpath(code_root)
        )
        detected["roots.code.*.path"] = "." if relative == "." else relative
        report.append({
            "reading": GIT_TREE,
            "answer": READ,
            "because":
                f"the work tree git reports is {top}, which is "
                f"{'the skills root itself' if relative == '.' else relative} "
                "from here",
        })

    remote = _git(code_root, "remote", "get-url", "origin") if top else None
    domain, slug = _slug(remote) if remote else (None, None)
    if slug:
        detected["host.kind"] = _kind_from(domain)
        detected["host.repo"] = slug
        report.append({
            "reading": GIT_REMOTE,
            "answer": READ,
            "because": f"the remote is {remote}, naming {domain} and {slug}",
        })
    else:
        report.append({
            "reading": GIT_REMOTE,
            "answer": UNESTABLISHED,
            "because": (
                "this root publishes no remote, so the host and the slug are asked"
                if remote is None else
                f"the remote {remote} is in no shape this module reads, so the "
                "host and the slug are asked rather than parsed out of it"
            ),
        })

    report.append(_definitions(skills_root, detected))
    report.append(_vocabularies(answers, menus))
    return {
        "code_root": code_root,
        "detected": detected,
        "menus": menus,
        "report": report,
    }


def _definitions(skills_root: str, detected: dict) -> dict:
    """The host's own workflow definitions, read where this toolkit can open them.

    ⛔ Where a host keeps them is read from the one statement of it in this
    toolkit -- the check that holds `host.checks` to those same files -- rather
    than spelled again here. A second directory here would read definitions the
    check never looks at, and the facet would then be generated against files
    nothing holds it to.
    """
    import check_host_checks

    kind = detected.get("host.kind")
    where = check_host_checks.DEFINITIONS.get(kind)
    if where is None:
        return {
            "reading": HOST_CLIENT,
            "answer": UNESTABLISHED,
            "because": (
                "the host kind is not established yet, so there is no directory "
                "to read definitions from" if kind is None else
                f"`{kind}` keeps its workflow definitions somewhere this toolkit "
                f"cannot open -- the kinds it can are "
                f"{', '.join(sorted(check_host_checks.DEFINITIONS))} -- so every "
                "check is asked rather than read"
            ),
        }
    directory = os.path.join(skills_root, where.directory)
    if not os.path.isdir(directory):
        return {
            "reading": HOST_CLIENT,
            "answer": NONE_STATED,
            "because":
                f"{where.directory} is not in this tree, so this project defines "
                "no workflow of its own yet and `host.checks` is an empty list "
                "rather than a reading that failed",
        }
    found = []
    for name in sorted(os.listdir(directory)):
        if not name.endswith(where.extensions):
            continue
        path = os.path.join(directory, name)
        try:
            with open(path, encoding="utf-8") as handle:
                text: str | Exception = handle.read()
        except OSError as error:  # pragma: no cover -- a permission, not logic
            text = error
        definition = check_host_checks.read_definition(text, path)
        if definition.name is check_host_checks.UNKNOWN:
            continue
        found.append({
            "workflow": definition.name,
            "triggers": (
                None if definition.triggers is check_host_checks.UNKNOWN
                else [check_host_checks.shown(one) for one in definition.triggers]
            ),
            "jobs": (
                None if definition.jobs is check_host_checks.UNKNOWN
                else sorted(definition.jobs)
            ),
            "definition": os.path.relpath(path, skills_root),
        })
    if found:
        detected["host.checks.workflow"] = [one["workflow"] for one in found]
        detected["host.checks.triggers"] = {
            one["workflow"]: one["triggers"] for one in found
        }
        detected["host.checks.jobs.job"] = {
            one["workflow"]: one["jobs"] for one in found
        }
    return {
        "reading": HOST_CLIENT,
        "answer": READ if found else NONE_STATED,
        "because": (
            f"{len(found)} workflow definition(s) under {where.directory}, each "
            "naming itself and its own triggers; what command each one runs is "
            "asked, nothing here holding the facet to a step"
            if found else
            f"{where.directory} holds no definition this reader can name, so "
            "`host.checks` is asked"
        ),
        "workflows": found,
    }


class _Provisional:
    """The answers so far, read the way a configuration is read.

    ⛔ A dotted-path getter and nothing else. The port binds a configuration to
    an adapter before every call, and what an adapter asks it for is the handful
    of keys that address the tracker -- so answering those is the whole of what a
    tracker can be interrogated through before a configuration exists.

    ⚠️ **Deliberately not a `Config`.** A real one is refused until every
    required key is written, which is exactly the state this step is in: a
    provisional view that went through the reader would be refused for want of
    the answers the interrogation is trying to make unnecessary.
    """

    def __init__(self, answers: dict):
        self._answers = answers

    def get(self, path: str, default=None):
        found = _at(self._answers, path)
        return default if found is None else found


def _vocabularies(answers: dict, menus: dict) -> dict:
    """The vocabularies the tracker itself states, through the port.

    ⛔ Through the port and never around it: the operation is the one seam a
    tracker is reached by, so a setup step that called a client directly would be
    a second implementation of every tracker this toolkit supports -- and one no
    capability query could report the absence of.
    """
    kind = _at(answers, "tracker.kind")
    if not kind:
        return {
            "reading": TRACKER_VOCABULARY,
            "answer": UNESTABLISHED,
            "because":
                "which tracker this project uses has not been answered yet, so "
                "there is nothing to interrogate. ⚠️ Not a failure: the tracker's "
                "own vocabularies are read once that question is answered, and "
                "this step is run again with it in hand",
        }
    try:
        tracker = tracker_port.Port(_Provisional(answers))
        if not tracker.implements(READ_VOCABULARY):
            return {
                "reading": TRACKER_VOCABULARY,
                "answer": UNESTABLISHED,
                "because":
                    f"`{kind}` does not implement `{READ_VOCABULARY}`, so "
                    f"{tracker.fallback(READ_VOCABULARY)}",
            }
        outcome = tracker.invoke(READ_VOCABULARY)
    except ConfigError as refused:
        return {
            "reading": TRACKER_VOCABULARY,
            "answer": UNESTABLISHED,
            "because":
                f"the tracker could not be addressed with the answers in hand: "
                f"{refused}",
        }
    if not outcome.performed:
        return {
            "reading": TRACKER_VOCABULARY,
            "answer": UNESTABLISHED,
            "because": outcome.detail,
        }
    published = outcome.result or {}
    for key, vocabulary in VOCABULARY_FOR.items():
        reading = published.get(vocabulary)
        if isinstance(reading, dict) and reading.get("answer") == READ:
            menus[key] = reading["values"]
    return {
        "reading": TRACKER_VOCABULARY,
        "answer": READ,
        "because":
            f"`{kind}` published "
            + ", ".join(
                f"{name} ({one.get('answer')})"
                for name, one in sorted(published.items())
            ),
        "vocabularies": published,
    }


# --- what the answers have to carry before anything is written --------------


def _answered_in(facts: dict, answers: dict):
    """Whether one required key is answered, in either of the two places § 1 allows.

    ⛔ **Two places rather than one, and neither is this module's invention.** A
    project whose code is one repository answers a key absolutely; a project
    carrying a collection of roots answers the per-root blocks § 1 names *under
    every entry*, and there is then no absolute answer to find. A check that
    looked only at the top would report a correctly-stated two-repository project
    as short of the keys it states twice.

    ⛔ **And a key the project names in § 28's own list is answered from outside
    the repository**, so its absence here is the facet working rather than a
    question nobody answered. Read off `private.keys` rather than off the
    surface's marks: the mark says a key *may* be resolved that way and the list
    says this project does.
    """
    per_root = facts["per_root"]
    roots = _at(answers, "roots.code")
    resolved_elsewhere = set(_at(answers, "private.keys") or [])

    def answered(path: str) -> bool:
        if path in resolved_elsewhere:
            return True
        if _at(answers, path) is not None:
            return True
        if path.split(".")[0] in per_root and isinstance(roots, dict) and roots:
            return all(_at(entry, path) is not None for entry in roots.values())
        return False

    return answered


def shortfall(surface_text: str, answers: dict) -> list[str]:
    """Every reason these answers cannot be written yet, each naming its key.

    ⛔ **All of them, then the refusal** -- the readiness gate's own discipline
    one role over: a project with four unanswered keys hears about all four
    rather than being sent back once per round trip.

    ⛔ **And a key the reader marks required is checked here as well as there.**
    Not a second statement of requiredness: the marker is read off the surface
    both times, and what this adds is that the refusal names the *question* that
    was not answered rather than the configuration that would not load.
    """
    facts = config.surface_facts(surface_text)
    problems = []

    for key in blocks(surface_text):
        if key not in answers:
            problems.append(
                f"{key}: the surface declares this block and the answers carry no "
                "statement of it. Every block is stated, an absent facet by its "
                "`carrier` and a stated reason -- an absence is a configuration "
                "rather than a gap."
            )

    answered = _answered_in(facts, answers)

    for path, heading in sorted(facts["required"].items()):
        if not answered(path):
            problems.append(
                f"{path}: marked `# required` under § {heading}, and no answer "
                "carries it."
            )

    for (path, on, value), heading in sorted(facts["required_when"].items()):
        if str(_at(answers, on)) != value:
            continue
        if not answered(path):
            problems.append(
                f"{path}: marked `# required_when: {on} = {value}` under "
                f"§ {heading}, this project states that value, and no answer "
                "carries it."
            )

    for facet in sorted(facts["absent_reason"]):
        if _at(answers, f"{facet}.carrier") != ABSENT:
            continue
        if _at(answers, f"{facet}.absent_reason") is None:
            problems.append(
                f"{facet}.absent_reason: the facet is stated absent and carries no "
                "reason. An absence is a stated decision here, never an unset "
                "value, so the carrier and the reason are answered together."
            )
    return problems


# --- the routing: a value a repository may not hold -------------------------


# A stand-in rather than somebody's own fact. ⛔ **Stated here and held to the
# sweep's own spelling by the suite rather than imported from it.** The sweep
# that forbids a committed private value lives with this repository's tools and
# not in the plugin, so an import would be a plugin reaching for a file no
# adopter has -- while two spellings free to disagree would mean this step
# routing a value that sweep reddens on, or leaving one it does not. What closes
# that is an arm of the suite below, which runs where both files exist.
A_PLACEHOLDER = re.compile(r"^(?:<.*>|[^\n]*[<…][^\n]*)$")


def _all_placeholders(value) -> bool:
    """Whether a whole answer is a statement of shape, at any depth.

    ⛔ **An empty container is not a statement of shape.** It names nothing, so
    it is neither a stand-in nor a value and is left where the project wrote it
    — which is the arm the three-shape form already had and this walk keeps.

    ⚠️ **Both halves of a mapping entry are read**, a client's name being as
    much the value as the rate beside it, and ⛔ **the recursion is the point**:
    a mapping of lists of stand-ins is a statement of shape exactly as a flat
    one is, and the shape test is what decides whether a value leaves the file
    whose job is to carry the shape.
    """
    if isinstance(value, dict):
        return bool(value) and all(
            _all_placeholders(key) and _all_placeholders(entry)
            for key, entry in value.items()
        )
    if isinstance(value, list):
        return bool(value) and all(map(_all_placeholders, value))
    return _a_placeholder(value)


def _a_placeholder(value) -> bool:
    """Whether this value is a stand-in rather than somebody's own fact."""
    return isinstance(value, str) and bool(A_PLACEHOLDER.match(value.strip()))


def routed(surface_text: str, answers: dict) -> tuple[dict, dict]:
    """`(what the tracked file carries, what § 28's own file carries)`.

    ⛔ Read off the surface's own `# private` mark rather than a list here, so a
    key marked after this module was written is routed without an edit. ⚠️ The
    tracked file still states the key's **shape** where the facet has one -- what
    moves is the value alone, which is § 28's own division.
    """
    facts = config.surface_facts(surface_text)
    tracked = json.loads(json.dumps(answers))  # a deep copy through plain data
    private: dict[str, object] = {}
    for path in sorted(facts["private"]):
        value = _at(answers, path)
        # ⛔ A key **stated empty** is not a key carrying a value, and it stays in
        # the tracked file. The surface's own rule -- a value stated empty is a
        # project's stated fact rather than a missing one -- and the sweep that
        # holds this half reads the same way: what it forbids is a *value* under
        # a private-marked key, and an empty list carries none. Routed out, the
        # project's statement that it reads no calendars at all would move into a
        # file nobody reviews.
        if value is None or value == [] or value == {} or value == "":
            continue
        # ⚠️ And a placeholder is not a value either, by the same reading the
        # sweep takes: a shape stating `<the exported archive>` is naming the key
        # rather than somebody's own archive, and routing it would move a
        # statement of shape out of the file whose job is to carry the shape.
        #
        # ⛔ **Three shapes and not two.** A mapping is here because § 37's
        # `rates` is the first private-marked key whose shape is one, and the
        # two-shape form routed it: both halves of its entries are stand-ins, so
        # a project illustrating the shape had its illustration moved into a file
        # nobody reviews -- and the write then refused for want of a layer that
        # project deliberately states none of. ⚠️ **Both halves are read**,
        # because a client's name is as much the value as the rate beside it.
        # ⚠️ **Read by shape rather than by depth.** The two-shape form, and the
        # three-shape one that replaced it, each tested one level: a list of
        # stand-ins and a mapping whose halves are stand-ins were read, and a
        # value one level further down was not -- so a nested illustration was
        # routed out, which is the same failure the three-shape form was written
        # to fix, reproduced one level down. ⛔ The walk below reaches any depth
        # and answers the same thing at every one of them.
        if _all_placeholders(value):
            continue
        private[path] = value
        _unset(tracked, path)
    return tracked, private


def _unset(data: dict, path: str) -> None:
    """Take one dotted path out of a nested block, pruning nothing else.

    ⚠️ The block the key sat in is left in place even where it empties: a project
    that states `evidence: {}` has said something, and a writer that pruned it
    would be deciding that an empty block means the same as an absent one.
    """
    head, _, rest = path.partition(".")
    if not isinstance(data, dict) or head not in data:
        return
    if not rest:
        del data[head]
        return
    _unset(data[head], rest)


# --- the write --------------------------------------------------------------
#
# ⛔ An **edit** of a file that is there and a **render** of one that is not, and
# the split is the rule rather than an optimisation. A project's own comments
# about its own facts are part of its configuration, as is the line terminator it
# is written with, and a round trip through a parser takes every one of them out
# with nothing reporting the loss.


def render(surface_text: str, answers: dict, *, mark: bool = True) -> str:
    """A configuration this project has never had, in the surface's block order.

    ⚠️ The order is the surface's own and is not alphabetical: a file a person
    then reads follows the document they read the keys in. ⛔ The marker goes at
    the head where this module wrote the file, and `mark=False` is for the one
    caller that is composing a comparison rather than a file.
    """
    order = [path.split(".")[0] for path in _in_surface_order(surface_text, inventory(surface_text))]
    seen: list[str] = []
    for key in order:
        if key not in seen:
            seen.append(key)
    blocks = [key for key in seen if key in answers]
    blocks += [key for key in answers if key not in blocks]
    body = "".join(
        yaml.safe_dump(
            {key: answers[key]}, sort_keys=False, allow_unicode=True, width=10 ** 6
        )
        for key in blocks
    )
    return ("\n".join(HEAD) + "\n" + body) if mark else body


def edited(text: str, answers: dict) -> tuple[str, list[str], list[str]]:
    """`(the new text, the paths that changed, the paths that could not be placed)`.

    ⛔ **Only the keys whose value differs are touched**, which is what makes a
    second run leave the tree byte-identical and a run on a configured project
    change nothing it was not asked to. Everything else -- comments, blank lines,
    key order, the terminator -- is the file's own and is not rewritten.

    ⛔ **A path this cannot place is reported rather than appended.** A key whose
    block is written in a shape this editor does not reach is a key a blind
    append would state **twice**, and a reader resolving the first copy would then
    read a configuration nobody wrote. ⚠️ Which is why the caller reads the edit
    back: a file that loads and does not carry the change is the second condition,
    and it exists because this one cannot be made total.
    """
    current = yaml.safe_load(text) or {}
    changed: list[str] = []
    unplaced: list[str] = []
    lines = text.splitlines(keepends=True)
    for path in _value_paths(answers):
        wanted = _at(answers, path)
        if _at(current, path) == wanted:
            continue
        at = _line_of(lines, path)
        if at is None:
            unplaced.append(path)
            continue
        indent = len(lines[at]) - len(lines[at].lstrip())
        ends = "\r\n" if lines[at].endswith("\r\n") else "\n"
        rendered = yaml.safe_dump(
            {path.rpartition(".")[2]: wanted},
            sort_keys=False, allow_unicode=True, width=10 ** 6,
        ).rstrip("\n")
        block = "".join(
            " " * indent + one + ends for one in rendered.splitlines()
        )
        lines[at:_end_of(lines, at, indent)] = [block]
        changed.append(path)
    return "".join(lines), changed, unplaced


def _value_paths(data, prefix: str = ""):
    """Every dotted path in an answers block that carries a value rather than a block.

    ⚠️ A list is a value here even where its members are blocks: a list is edited
    whole, because an entry's position carries meaning the facets state -- the
    ordering of `statuses`, `readiness` and `done` each do -- and an editor that
    reached inside one would be choosing which entry a path names.
    """
    if not isinstance(data, dict):
        return
    for key, value in data.items():
        path = f"{prefix}{key}"
        if isinstance(value, dict) and value:
            yield from _value_paths(value, f"{path}.")
        else:
            yield path


def _line_of(lines: list[str], path: str) -> int | None:
    """The index of the line stating this path, or `None` where it is not there.

    ⛔ **A child is looked for strictly inside its parent's own block**, which
    means both of two bounds rather than one: the search stops at the next line
    indented no deeper than the parent, and it skips any line not indented deeper
    than it. Without the first, a search for a key the parent does not have runs
    on into whatever block comes next and edits a key of the same name there --
    which depends on nothing but the order a project happened to write its blocks
    in, and is therefore the kind of defect that holds on one file and not on the
    next.
    """
    want = path.split(".")
    found = None
    at, outer = 0, -1
    for depth, segment in enumerate(want):
        found = None
        for index in range(at, len(lines)):
            match = KEY_LINE.match(lines[index])
            if not match:
                continue
            indent = len(match.group("indent"))
            if depth and indent <= outer:
                break
            if depth and indent > outer and match.group("key") == segment:
                found, outer = index, indent
                break
            if not depth and indent == 0 and match.group("key") == segment:
                found, outer = index, indent
                break
        if found is None:
            return None
        at = found + 1
    return found


def _end_of(lines: list[str], at: int, indent: int) -> int:
    """One past the last line belonging to the key stated at `at`."""
    for index in range(at + 1, len(lines)):
        stripped = lines[index].strip()
        if not stripped:
            continue
        if len(lines[index]) - len(lines[index].lstrip()) <= indent:
            return index
    return len(lines)


def write(skills_root: str, answers: dict, *, dry_run: bool = False) -> dict:
    """The configuration, and § 28's own file where the answers carry one.

    ⛔ **Nothing is written unless every answer holds**, which is the release
    carrier's rule one artifact over and for the same reason: a configuration
    half written is worse than one not written, because the half that landed is
    what every later reader believes.

    ⛔ **And the edit is read back on two conditions rather than one**: a file
    that stops loading is put back, and so is a file that loads and **does not
    carry the change**. The second is not the first -- a configuration can state
    a key twice, where the text an edit went into is not the text the reader
    resolves -- and without it this step would report a clean write while leaving
    the resolved value untouched.
    """
    surface = config.surface_for(skills_root)
    with open(surface, encoding="utf-8") as handle:
        surface_text = handle.read()

    answer: dict = {
        "skills_root": os.path.abspath(skills_root),
        "configuration": config.CONFIG_PATH,
        "holds": False,
        "written": [],
        "changed": [],
        "report": [],
    }

    standing = shortfall(surface_text, answers)
    if standing:
        answer["report"] = standing
        answer["report"].insert(
            0,
            "Nothing was written: the answers do not carry what the surface asks "
            "for, and every key that is short is named below.",
        )
        answer["unanswered"] = True
        return answer

    tracked, private = routed(surface_text, answers)
    if private and _at(tracked, "private.carrier") != config.PRIVATE_FILE:
        answer["report"].append(
            "private.carrier: the answers carry a value at "
            + ", ".join(f"`{key}`" for key in sorted(private))
            + ", each marked `# private` on the surface, and this project states "
            "no file to resolve them from. A value a repository may not hold is "
            "routed to § 28's own file or it is not collected at all -- it is "
            "never written into the tracked one."
        )
        return answer

    # ⛔ Through the reader before anything is written, and that is the one
    # validation this module performs by asking rather than by checking: the
    # reader is what every role resolves a configuration with, so a file this
    # step wrote and the reader refuses is a project adopted into a state no role
    # can run in.
    rendered_whole = render(surface_text, tracked, mark=False)
    try:
        config.load_text(rendered_whole, skills_root, check_paths=False)
    except (ConfigError, OSError) as refused:
        answer["report"].append(
            f"the answers do not resolve through the reader every role runs on: "
            f"{refused}. Nothing was written."
        )
        return answer

    path = os.path.join(skills_root, config.CONFIG_PATH)
    existing = None
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as handle:
            existing = handle.read()

    if existing is None:
        composed = render(surface_text, tracked)
        answer["changed"] = sorted(_value_paths(tracked))
        answer["report"].append(
            f"{config.CONFIG_PATH} is not in this tree, so it is rendered whole "
            "and carries this module's head marker."
        )
    else:
        composed, changed, unplaced = edited(existing, tracked)
        answer["changed"] = changed
        if unplaced:
            answer["report"].append(
                "these keys could not be placed in the file that is there: "
                + ", ".join(f"`{key}`" for key in unplaced)
                + ". A key appended blind would be stated twice, and the reader "
                "resolves one of the two copies -- so nothing was written and the "
                "keys are named for whoever edits the file."
            )
            return answer
        if not changed:
            answer["holds"] = True
            answer["report"].append(
                f"{config.CONFIG_PATH} already carries every answer, so nothing "
                "was written and the tree is unchanged. ⚠️ Asserted on the bytes "
                "rather than reported: the file is not rewritten at all."
            )
            return answer
        answer["report"].append(
            f"{config.CONFIG_PATH} is edited key by key: "
            + ", ".join(f"`{key}`" for key in changed)
            + ". Its comments, its key order and its terminator are its own and "
            "are not rewritten."
        )

    # The read-back, taken against the text that is about to be written rather
    # than after writing it: a refusal then costs nothing, where a refusal after
    # the write costs a restore.
    try:
        loaded = config.load_text(composed, skills_root, check_paths=False)
    except (ConfigError, OSError) as refused:
        answer["report"].append(
            f"the edit would leave a file the reader refuses: {refused}. Nothing "
            "was written."
        )
        return answer
    # ⛔ A key the project resolves from § 28's own file is **not** read back
    # here, and that is the facet rather than a gap: the tracked file states its
    # shape and the value comes from a file this step has not written yet, so a
    # comparison against the tracked text would refuse every project with a
    # private layer. ⚠️ And a key the reader cannot resolve at all is reported as
    # unread rather than as wrong -- § 11's rule, and the write proceeds because
    # it is an act that can be made again.
    resolved_elsewhere = set(_at(tracked, "private.keys") or [])
    missing, unread = [], []
    for key in answer["changed"]:
        if key in resolved_elsewhere:
            continue
        try:
            got = loaded.get(key)
        except (ConfigError, OSError) as refused:
            unread.append(f"`{key}` ({refused})")
            continue
        if got != _at(tracked, key):
            missing.append(key)
    if unread:
        answer["report"].append(
            "the edit could not be read back for " + ", ".join(unread)
            + ". ⛔ Not read as agreement: what the reader resolves for those keys "
            "is unestablished, and the write below is an act that can be made "
            "again."
        )
    if missing:
        answer["report"].append(
            "the edit would leave a file that loads and does not carry "
            + ", ".join(f"`{key}`" for key in missing)
            + " -- the text it went into is not the text the reader resolves, "
            "which a configuration stating a key twice produces. Nothing was "
            "written."
        )
        return answer

    answer["holds"] = True
    if dry_run:
        answer["report"].append(
            "Nothing was written: this was a plan. The report above is what the "
            "write would do."
        )
        return answer

    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(composed)
    answer["written"].append(config.CONFIG_PATH)

    if private:
        where = _at(tracked, "private.source")
        full = where if os.path.isabs(where) else os.path.join(skills_root, where)
        full = os.path.expanduser(os.path.expandvars(full))
        os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(yaml.safe_dump(
                {key: value for key, value in sorted(private.items())},
                sort_keys=False, allow_unicode=True,
            ))
        answer["written"].append(where)
        answer["report"].append(
            f"{len(private)} value(s) a repository may not hold went to {where} "
            "and to no tracked file (§ 28)."
        )
    return answer


def unmark(skills_root: str) -> dict:
    """Take this module's head marker out, leaving the configuration itself.

    ⛔ **The marker and never the file.** Removing a project's configuration is
    removing its adoption, which is a person's act rather than a step's -- so
    what is removable here is the claim that this module wrote the file, which is
    one of the things that has to be unpicked when a plugin is retired.
    """
    path = os.path.join(skills_root, config.CONFIG_PATH)
    if not os.path.isfile(path):
        return {"holds": False, "report": [
            f"{config.CONFIG_PATH} is not in this tree, so there is no marker to "
            "take out."
        ]}
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    if not _marked(text):
        return {"holds": True, "report": [
            f"{config.CONFIG_PATH} carries no marker of this module's, so nothing "
            "was changed. ⚠️ Not a failure: a file a person wrote is edited key by "
            "key here and never marked, so an unmarked configuration is the "
            "ordinary state of a project that was configured by hand."
        ]}
    lines = text.splitlines(keepends=True)
    kept = [line for line in lines[:2] if f"{MARKER}:" not in line
            and "edits here are kept" not in line]
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("".join(kept + lines[2:]))
    return {"holds": True, "report": [
        f"the head marker was taken out of {config.CONFIG_PATH}; the "
        "configuration itself is untouched."
    ]}


# --- the state this project is in ------------------------------------------


def state(skills_root: str) -> dict:
    """Whether this project is configured, what was read, and what still stands.

    ⚠️ A project that states no configuration is **told so** rather than left to
    read a silence: this step is invoked by name, and § 7 makes that answer owed
    to whoever invokes a role in a project configuring nothing.
    """
    surface = config.surface_for(skills_root)
    with open(surface, encoding="utf-8") as handle:
        surface_text = handle.read()
    configured = config.configured(skills_root)
    answers: dict = {}
    if configured:
        path = os.path.join(skills_root, config.CONFIG_PATH)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        answers = yaml.safe_load(text) or {}
        marked = _marked(text)
    else:
        marked = False
    seen = interrogate(skills_root, answers)
    standing = questions(surface_text, answers, seen["detected"], seen["menus"])
    return {
        "skills_root": os.path.abspath(skills_root),
        "configured": configured,
        "marked": marked,
        "code_root": seen["code_root"],
        "interrogation": seen["report"],
        "detected": seen["detected"],
        "questions_standing": len(standing),
        "keys_in_the_surface": len(inventory(surface_text)),
        "coverage": coverage(surface_text),
        "shortfall": shortfall(surface_text, answers) if configured else [],
        "report": [] if configured else [
            "This project states no configuration, so nothing here is adopted "
            f"yet. What the setup role writes is {config.CONFIG_PATH}, relative to "
            "the skills root, and every key it carries is stated in the "
            "configuration surface shipped with the toolkit."
        ],
    }


# --- the suite -------------------------------------------------------------


# The user part of a remote this suite reads, kept apart from the host it is
# joined to. ⛔ Never written beside a domain in this file: see the fixtures that
# compose the two.
A_USER = "a-user"


def _a_tree(files: dict[str, str]) -> str:
    """A tree carrying the files named, for a plant to be taken against."""
    root = tempfile.mkdtemp(prefix="mjolnir-setup-")
    for name, text in files.items():
        full = os.path.join(root, name)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as handle:
            handle.write(text)
    return root


def _an_example(name: str) -> dict:
    """One shipped example read as an answers block.

    ⛔ Composed off a shipped example rather than written here, for the reason
    every fixture beside this module is: a configuration written out in full
    would stop asserting the moment a key became required elsewhere, and the half
    of it that is a *fixture* would be invisible.
    """
    with open(os.path.join(config.EXAMPLES, name), encoding="utf-8") as handle:
        return yaml.safe_load(handle.read())


def _examples() -> list[str]:
    return sorted(
        name for name in os.listdir(config.EXAMPLES)
        if name.endswith((".yaml", ".yml"))
    )


def self_test() -> int:
    failures = []

    def check(label: str, held: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if held else 'FAIL'}  {label}" + (
            "" if held else f": {detail}"))
        if not held:
            failures.append(label)

    with open(config.SURFACE, encoding="utf-8") as handle:
        surface_text = handle.read()
    declared = inventory(surface_text)

    print("Every facet the surface states has a question behind it:")
    problems = coverage(surface_text)
    check("the surface and this module's table agree", not problems,
          "; ".join(problems[:4]))
    check("and the walk reaches more than a handful of keys",
          len(declared) > 100, f"reached {len(declared)}")

    # ⛔ The arm the acceptance condition names, and the one that makes the
    # coverage check a *check* rather than a snapshot: a facet added to the
    # surface after this ships reddens until this module asks for it. ⚠️ Planted
    # into a copy of the surface rather than into the file, because the undo for
    # a deliberate break is a copy and not version control's own checkout of one.
    grown = surface_text.replace(
        "environment:\n",
        "environment:\n  a_facet_nobody_asked_about: \"\"   # required\n",
        1,
    )
    check("a facet added to the surface reddens this module",
          any("a_facet_nobody_asked_about" in line for line in coverage(grown)),
          f"said {coverage(grown)[:2]!r}")

    # ⛔ And the other direction, which the first arm cannot see: an entry naming
    # a key the surface no longer declares is a question about a facet that is
    # gone. Measured while this module was being written -- one such entry.
    retired = surface_text.replace("  prose_width:", "  retired_width:", 1)
    check("a facet taken off the surface reddens it too",
          any("language.prose_width" in line for line in coverage(retired)),
          f"said {coverage(retired)[:2]!r}")

    print("\nThe nine keys a list entry opens with, which the reader does not yield:")
    entries = entry_keys(surface_text)
    check("the entry walk finds the keys written on a `- ` line",
          "host.checks.workflow" in entries and "test_tiers.tiers.tier" in entries,
          f"found {sorted(entries)!r}")
    check("and every one of them is in the inventory the coverage walks",
          set(entries) <= set(declared) | {
              path.rsplit(".", 1)[0] for path in declared if "." in path
          },
          f"outside it: {sorted(set(entries) - set(declared))!r}")

    print("\nA question carries what the surface states about its key, and no more:")
    asked = {one["key"]: one for one in questions(surface_text)}
    check("a key whose surface line states an alternation carries it as its menu",
          asked["branch_model.kind"]["menu"] == ["worktree", "in_place"],
          f"carried {asked['branch_model.kind']['menu']!r}")
    check("and says the menu came from the surface",
          asked["branch_model.kind"]["menu_from"] == "the surface",
          f"said {asked['branch_model.kind']['menu_from']!r}")
    check("a key marked `# required` says so",
          asked["host.repo"]["required"], f"carried {asked['host.repo']!r}")
    check("a key marked `# required_when` carries its condition",
          asked["tracker.board"]["required_when"] == ["tracker.kind = trello"],
          f"carried {asked['tracker.board']['required_when']!r}")
    check("a key marked `# private` says so",
          asked["day_log.attribute_to"]["private"],
          f"carried {asked['day_log.attribute_to']!r}")
    check("a carrier question whose facet may be absent names the facet",
          asked["release.carrier"]["absent_case"] == "release",
          f"carried {asked['release.carrier']['absent_case']!r}")
    check("a key the surface marks a default for carries it",
          asked["context_guard.reread"]["has_default"]
          and asked["context_guard.reread"]["default"] == "refuse",
          f"carried {asked['context_guard.reread']!r}")
    check("the first questions are about where the code is",
          questions(surface_text)[0]["key"].startswith("roots."),
          f"opened with {questions(surface_text)[0]['key']!r}")

    # ⛔ *Detect what is detectable, ask the rest*: a key the interrogation
    # answered is dropped rather than put with a suggestion beside it.
    fewer = {one["key"] for one in questions(
        surface_text, detected={"host.repo": "a/b"})}
    check("a key the interrogation answered is not asked",
          "host.repo" not in fewer, "it was asked anyway")
    carried = {one["key"] for one in questions(
        surface_text, answers={"host": {"repo": "a/b"}})}
    check("and neither is one the answers already carry",
          "host.repo" not in carried, "it was asked anyway")

    # ⚠️ A vocabulary the tracker published wins over the surface's own set, and
    # it is the menu rather than the value -- so the question stays.
    with_menu = {one["key"]: one for one in questions(
        surface_text, menus={"statuses": ["Todo", "Doing", "Done"]})}
    check("a tracker's own vocabulary becomes the menu of the key it answers",
          with_menu["statuses"]["menu"] == ["Todo", "Doing", "Done"],
          f"carried {with_menu['statuses']['menu']!r}")
    check("and the question is still put, a vocabulary being a candidate set",
          "statuses" in with_menu, "the question was dropped")
    check("while the question says the menu is the tracker's",
          with_menu["statuses"]["menu_from"] == "the tracker",
          f"said {with_menu['statuses']['menu_from']!r}")

    print("\nThe absent word, held against every facet that has an absent case:")
    facts = config.surface_facts(surface_text)
    wrong = [
        facet for facet in facts["absent_reason"]
        if ABSENT not in (facts["enums"].get(f"{facet}.carrier") or [])
    ]
    check("every absent-capable facet's carrier states the one absent word",
          not wrong, f"these do not: {sorted(wrong)!r}")

    print("\nWhat the answers have to carry before anything is written:")
    for name in _examples():
        standing = shortfall(surface_text, _an_example(name))
        check(f"{name} carries everything the surface asks for", not standing,
              "; ".join(standing[:3]))

    short = _an_example("none.yaml")
    del short["environment"]
    check("a block the surface declares and the answers omit is named",
          any("environment" in line for line in shortfall(surface_text, short)),
          f"said {shortfall(surface_text, short)[:2]!r}")

    short = _an_example("none.yaml")
    del short["host"]["repo"]
    check("a key marked required and left unanswered is named",
          any("host.repo" in line for line in shortfall(surface_text, short)),
          f"said {shortfall(surface_text, short)[:2]!r}")

    short = _an_example("trello.yaml")
    del short["tracker"]["board"]
    check("a conditionally required key is named where its condition holds",
          any("tracker.board" in line for line in shortfall(surface_text, short)),
          f"said {shortfall(surface_text, short)[:2]!r}")
    # ⚠️ The green side of the same condition, which is what keeps it a condition
    # rather than a requirement: the same key unanswered on another tracker is no
    # shortfall at all.
    other = _an_example("jira.yaml")
    check("and is not named where the condition does not hold",
          not any("tracker.board" in line for line in shortfall(surface_text, other)),
          f"said {shortfall(surface_text, other)[:2]!r}")

    short = _an_example("none.yaml")
    short["release"] = {"carrier": ABSENT}
    check("a facet stated absent with no reason is named",
          any("release.absent_reason" in line
              for line in shortfall(surface_text, short)),
          f"said {shortfall(surface_text, short)[:2]!r}")

    print("\nA value a repository may not hold reaches § 28's file and no other:")
    # ⛔ The arm that keeps the placeholder form from being a second spelling: the
    # sweep forbidding a committed private value carries the same form, and the
    # two agree here or this suite says so. ⚠️ Skipped rather than failed where
    # that file is not beside this one, which is an adopter's tree: the plugin
    # ships without this repository's own tools.
    sweep = os.path.join(config.REPO_ROOT, "tools", "check_no_project_names.py")
    if os.path.isfile(sweep):
        sys.path.insert(0, os.path.dirname(sweep))
        import check_no_project_names  # noqa: E402 -- held to, not depended on

        check("the placeholder form is the one the private-value sweep reads",
              check_no_project_names.PLACEHOLDER.pattern == A_PLACEHOLDER.pattern,
              f"the sweep reads {check_no_project_names.PLACEHOLDER.pattern!r} "
              f"and this module reads {A_PLACEHOLDER.pattern!r}")
    else:  # pragma: no cover -- an adopter's tree rather than this repository
        print("  --    the private-value sweep is not beside this file, so the "
              "placeholder form is held to nothing here")

    answers = _an_example("none.yaml")
    answers["day_log"]["attribute_to"] = "a person"
    answers["private"] = {
        "carrier": config.PRIVATE_FILE,
        "source": "private.yaml",
        "keys": ["day_log.attribute_to"],
    }
    tracked, private = routed(surface_text, answers)
    check("the private-marked value is out of what the tracked file carries",
          _at(tracked, "day_log.attribute_to") is None,
          f"the tracked block still carries {_at(tracked, 'day_log.attribute_to')!r}")
    check("and it is in what the untracked file carries",
          private == {"day_log.attribute_to": "a person"}, f"routed {private!r}")
    check("the block it sat in is left in place rather than pruned",
          "day_log" in tracked, "the block was pruned")

    # ⛔ § 37's `rates` is the first private-marked key shaped as a **mapping**,
    # and both directions are asserted because the shape test had two arms and
    # needed three. ⚠️ The green side first: a mapping of stand-ins states the
    # key's shape and stays in the tracked file, which is what a project with no
    # § 28 layer writes -- and routing it refused that project's own write.
    shaped = _an_example("none.yaml")
    shaped["billing"] = {
        "carrier": "period",
        "projects": ["/a-project"],
        "rates": {"<the client an invocation names>": "<that client's rate>"},
    }
    tracked, private = routed(surface_text, shaped)
    check("a private-marked mapping of stand-ins stays in the tracked file",
          _at(tracked, "billing.rates") is not None and "billing.rates" not in private,
          f"routed {private!r}")

    # ⛔ And the red side, which is what the arm is for: a mapping carrying
    # somebody's own client and rate is a value, and it moves. ⚠️ Asserted
    # because a shape test written only on the green side would pass with the
    # whole arm inverted.
    real = json.loads(json.dumps(shaped))
    real["billing"]["rates"] = {"a-client": 100}
    real["private"] = {
        "carrier": config.PRIVATE_FILE,
        "source": "private.yaml",
        "keys": ["billing.rates"],
    }
    tracked, private = routed(surface_text, real)
    check("a private-marked mapping carrying real values is routed out",
          _at(tracked, "billing.rates") is None
          and private == {"billing.rates": {"a-client": 100}},
          f"routed {private!r}, tracked {_at(tracked, 'billing.rates')!r}")
    check("a mapping with a real client and a stand-in rate is routed too",
          "billing.rates" in routed(
              surface_text,
              {**real, "billing": {**real["billing"],
                                   "rates": {"a-client": "<that client's rate>"}}},
          )[1],
          "a half-stated mapping stayed in the tracked file")

    # ⛔ And the depth, which is what the shape test is read by. ⚠️ **Measured
    # on the three-shape form**: a mapping whose entries are themselves
    # stand-in containers was routed out, which is the same failure that form
    # was written to fix, one level down.
    nested = _an_example("none.yaml")
    nested["billing"] = {
        "carrier": "period",
        "projects": ["/a-project"],
        "rates": {"<the client an invocation names>": ["<that client's rate>"]},
    }
    tracked, private = routed(surface_text, nested)
    check("a stand-in nested one level deeper still states shape, so it stays",
          _at(tracked, "billing.rates") is not None
          and "billing.rates" not in private,
          f"routed {private!r}")

    # ⛔ And a project with a private value and no private layer is **refused**:
    # the one thing that must never happen is the value landing in the tracked
    # file for want of anywhere else to put it.
    answers = _an_example("none.yaml")
    answers["day_log"]["attribute_to"] = "a person"
    root = _a_tree({})
    written = write(root, answers)
    check("a private value with no private layer stated refuses the write",
          not written["holds"], "the write held")
    check("and the refusal names the key and the facet",
          any("day_log.attribute_to" in line and "private.carrier" in line
              for line in written["report"]),
          f"said {written['report']!r}")
    check("with nothing written at all",
          not os.path.exists(os.path.join(root, config.CONFIG_PATH)),
          "a file was written")

    print("\nA project that has never seen the toolkit, once per tracker:")
    for name in _examples():
        answers = _an_example(name)
        root = _a_tree({})
        written = write(root, answers)
        if not written["holds"]:
            check(f"{name} is written into a fresh tree", False,
                  "; ".join(written["report"][:2]))
            continue
        path = os.path.join(root, config.CONFIG_PATH)
        with open(path, encoding="utf-8") as handle:
            text = handle.read()
        refusal = None
        try:
            config.load_text(text, root, check_paths=False)
        except (ConfigError, OSError) as refused:
            refusal = str(refused)
        check(f"{name} is written into a fresh tree and the reader accepts it",
              refusal is None, f"refused with {refusal!r}")
        check(f"{name}'s file carries the head marker", _marked(text),
              "no marker at its head")
        # ⛔ Idempotence, asserted on the **bytes**: a second run leaves the file
        # byte-identical, which is what makes re-running this step on a
        # configured project safe rather than merely reported as safe.
        again = write(root, answers)
        with open(path, encoding="utf-8") as handle:
            after = handle.read()
        check(f"{name} re-written changes nothing it was not asked to",
              again["holds"] and after == text and not again["changed"],
              f"changed {again.get('changed')!r}")

    print("\nA configured project, edited key by key:")
    root = _a_tree({})
    answers = _an_example("github-issues.yaml")
    write(root, answers)
    path = os.path.join(root, config.CONFIG_PATH)
    with open(path, encoding="utf-8") as handle:
        before = handle.read()
    # A comment and a blank line a project would have added itself, which a round
    # trip through a parser takes out with nothing reporting the loss.
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(before.replace(
            "language:", "# the register below was argued out with the team\nlanguage:", 1))
    answers["language"]["prose_width"] = 92
    written = write(root, answers)
    with open(path, encoding="utf-8") as handle:
        after = handle.read()
    check("the one key asked for is the only one reported changed",
          written["changed"] == ["language.prose_width"],
          f"changed {written['changed']!r}")
    check("the project's own comment is still there",
          "argued out with the team" in after, "the comment was taken out")
    check("and the key the edit was asked for carries the new value",
          config.load_text(after, root, check_paths=False).get(
              "language.prose_width") == 92,
          "the reader resolves something else")

    # ⛔ The second read-back condition, which is **not** the first: this file
    # loads clean, so nothing refuses it, and the text an edit goes into is not
    # the text the reader resolves. Planted by hand because no answers block
    # produces it -- a key stated twice inside one block, where the parser takes
    # the last and this editor finds the first.
    #
    # ⚠️ The plant is a *duplicate inside the same block* rather than a second
    # block appended at the end: the appended form replaces the whole block and
    # is then refused for the keys it drops, which is the **first** condition
    # firing and would leave this arm asserting nothing. Measured while this
    # suite was being written.
    doubled = _a_tree({config.CONFIG_PATH: before.replace(
        "  prose_width: 100\n", "  prose_width: 100\n  prose_width: 70\n", 1)})
    assert "prose_width: 70" in open(
        os.path.join(doubled, config.CONFIG_PATH), encoding="utf-8").read(), (
        "the plant did not go in, so this arm would assert nothing"
    )
    answers["language"]["prose_width"] = 55
    written = write(doubled, answers)
    check("a file that loads and does not carry the change refuses the write",
          not written["holds"], "the write held")
    check("and says so rather than reporting a clean write",
          any("does not carry" in line for line in written["report"]),
          f"said {written['report']!r}")

    # ⛔ The bound the child search is strict for, and the one defect of this
    # editor measured by review rather than by a failing case: asked for a key
    # one block does not have, a search that stopped only at column zero ran on
    # into the **sibling** block and edited a key of that name there. Planted
    # with two sibling blocks at one depth, each holding a key the other does
    # not: `landing` has no `kind` and `runs` has one.
    siblings = (
        "host:\n"
        "  landing:\n"
        "    method: squash\n"
        "  runs:\n"
        "    kind: github\n"
    )
    out, changed, unplaced = edited(
        siblings, {"host": {"landing": {"kind": "a-kind"}}})
    check("a key one block does not have is not found in the block beside it",
          unplaced == ["host.landing.kind"] and not changed and out == siblings,
          f"changed {changed!r}, left {out!r}")
    check("while the key the block does have is still reached",
          edited(siblings, {"host": {"runs": {"kind": "a-kind"}}})[1]
          == ["host.runs.kind"],
          f"changed {edited(siblings, {'host': {'runs': {'kind': 'x'}}})[1]!r}")

    # ⚠️ The one thing an edit does **not** keep, stated as a bound rather than
    # found later: a key whose value is a list is replaced whole -- an entry's
    # position carries meaning the facets state -- so a comment written *inside*
    # that list does not survive an edit of it. A comment anywhere else does.
    with_a_note = (
        "host:\n"
        "  checks:\n"
        "    # the first of these was argued out with the team\n"
        "    - workflow: \"A check\"\n"
        "  kind: github\n"
    )
    out, changed, _ = edited(
        with_a_note, {"host": {"checks": [{"workflow": "Another"}]}})
    check("a comment inside a list does not survive an edit of that list",
          changed == ["host.checks"] and "argued out" not in out,
          f"left {out!r}")
    check("while the keys beside the list are untouched",
          "kind: github" in out, f"left {out!r}")

    print("\nWhat the interrogation reads, and what it reports it could not:")
    root = _a_tree({})
    seen = interrogate(root)
    check("a tree that is not a repository is reported unestablished",
          any(one["reading"] == GIT_TREE and one["answer"] == UNESTABLISHED
              for one in seen["report"]),
          f"reported {seen['report']!r}")
    check("and nothing is detected from it rather than a root being guessed",
          "roots.code.*.path" not in seen["detected"],
          f"detected {seen['detected']!r}")

    # ⛔ A repository whose own directory is reached through a symlink, which is
    # the ordinary state of a temporary tree on at least one system this runs on.
    # git answers with the resolved path and a skills root keeps what the caller
    # wrote, so an unresolved comparison reports the root as a stack of `..`
    # segments -- written into `roots.code`, that is the path every later call
    # addresses. Measured as a defect in this module rather than argued.
    repository = _a_tree({})
    started = subprocess.run(["git", "init", "-q", repository],
                             capture_output=True, text=True)
    if started.returncode == 0:
        seen = interrogate(repository)
        check("a root reached through a symlink still reads as the root itself",
              seen["detected"].get("roots.code.*.path") == ".",
              f"detected {seen['detected'].get('roots.code.*.path')!r}")
    else:  # pragma: no cover -- a runner with no git on the path
        print("  --    git is not on this path, so the root reading is held to "
              "nothing here")

    for remote, wanted in (
        ("https://a-host.example/an-owner/a-name.git", ("a-host", "an-owner/a-name")),
        # ⚠️ The two forms carrying a user before the host are **composed** rather
        # than written: the sweep that forbids an address in a tracked file reads
        # `word@domain` wherever it appears, and a fixture of that shape reddens
        # it however fictional the domain is. Measured -- the first form of these
        # two lines did. ⛔ Composed and not dropped: the shapes a host publishes
        # are what this reading has to cover, and the one that looks least like a
        # URL is the one a project is likeliest to have.
        (A_USER + "@a-host.example:an-owner/a-name.git",
         ("a-host", "an-owner/a-name")),
        ("ssh://" + A_USER + "@a-host.example:22/an-owner/a-name",
         ("a-host", "an-owner/a-name")),
    ):
        domain, slug = _slug(remote)
        check(f"the slug is read out of {remote}",
              (_kind_from(domain), slug) == wanted,
              f"read {(_kind_from(domain), slug)!r}")
    check("a remote in no shape this reads leaves both unestablished",
          _slug("this is not a remote") == (None, None),
          f"read {_slug('this is not a remote')!r}")

    # ⛔ The tracker half, with no tracker answered yet: reported as nothing to
    # interrogate rather than as a tracker that answered nothing.
    nothing = _vocabularies({}, {})
    check("with no tracker answered, the vocabularies are unestablished",
          nothing["answer"] == UNESTABLISHED, f"answered {nothing!r}")
    check("and the reason says the question has not been answered yet",
          "has not been answered" in nothing["because"],
          f"said {nothing['because']!r}")

    print("\nThe head marker: at the head, not moving, and removable:")
    root = _a_tree({})
    write(root, _an_example("none.yaml"))
    path = os.path.join(root, config.CONFIG_PATH)
    with open(path, encoding="utf-8") as handle:
        text = handle.read()
    check("nothing in the marker moves between runs",
          not re.search(r"\d{4}-\d{2}-\d{2}|\bv?\d+\.\d+\.\d+\b", "\n".join(HEAD)),
          f"the marker carries {HEAD!r}")
    taken = unmark(root)
    with open(path, encoding="utf-8") as handle:
        bare = handle.read()
    check("unmarking takes the marker out", taken["holds"] and not _marked(bare),
          f"left {bare.splitlines()[:2]!r}")
    check("and leaves the configuration itself loading",
          config.load_text(bare, root, check_paths=False).get("tracker.kind")
          == config.load_text(text, root, check_paths=False).get("tracker.kind"),
          "the configuration changed")
    # ⚠️ A file a person wrote carries no marker, which is the ordinary state of
    # a project configured by hand -- so unmarking one is not a failure.
    again = unmark(root)
    check("unmarking a file that carries none changes nothing and is not a failure",
          again["holds"] and any("carries no marker" in line
                                 for line in again["report"]),
          f"said {again['report']!r}")
    check("a marker quoted anywhere but the head is not read as one",
          not _marked("tracker:\n  kind: none\n# " + MARKER + ": quoted\n"),
          "a quoted marker read as this module's own")

    print("\nThis project's own answer:")
    try:
        answer = state(config.REPO_ROOT)
    except (ConfigError, OSError) as exc:
        check("this project's own state reads back", False, str(exc))
    else:
        check("this project is configured and its answers hold",
              answer["configured"] and not answer["shortfall"],
              f"said {answer['shortfall'][:3]!r}")
        check("and the surface and this module agree about it",
              not answer["coverage"], f"said {answer['coverage'][:2]!r}")
        print(f"        {answer['keys_in_the_surface']} keys in the surface, "
              f"{answer['questions_standing']} question(s) standing")
        for one in answer["interrogation"]:
            print(f"        {one['reading']}: {one['answer']} -- {one['because']}")

    print()
    if failures:
        print(f"{len(failures)} failed: " + "; ".join(failures))
        return 1
    print("all held")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "what", nargs="?", choices=["questions", "interrogate", "write", "unmark"]
    )
    parser.add_argument("--skills-root", default=None)
    parser.add_argument("--answers", default=None)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()

    root = args.skills_root or os.getcwd()
    answers: dict = {}
    if args.answers:
        with open(args.answers, encoding="utf-8") as handle:
            answers = yaml.safe_load(handle.read()) or {}
        if not isinstance(answers, dict):
            parser.error(f"{args.answers} is not a block of keys.")

    try:
        surface = config.surface_for(root)
        with open(surface, encoding="utf-8") as handle:
            surface_text = handle.read()
    except OSError as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.what == "unmark":
        answer = unmark(root)
        print(json.dumps(answer, indent=2, ensure_ascii=False))
        return 0 if answer["holds"] else 1

    if args.what == "interrogate":
        print(json.dumps(interrogate(root, answers), indent=2, ensure_ascii=False))
        return 0

    if args.what == "questions":
        seen = interrogate(root, answers)
        standing = questions(
            surface_text, answers or None, seen["detected"], seen["menus"]
        )
        print(json.dumps({
            "keys_in_the_surface": len(inventory(surface_text)),
            "detected": seen["detected"],
            "interrogation": seen["report"],
            "questions": standing,
        }, indent=2, ensure_ascii=False))
        return 0 if not standing else UNANSWERED

    if args.what == "write":
        if not args.answers:
            parser.error("`write` needs the answers to write: --answers FILE")
        answer = write(root, answers, dry_run=args.dry_run)
        print(json.dumps(answer, indent=2, ensure_ascii=False))
        if answer["holds"]:
            return 0
        return UNANSWERED if answer.get("unanswered") else 1

    answer = state(root)
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    if answer["coverage"]:
        return 1
    return UNANSWERED if answer["questions_standing"] else 0


if __name__ == "__main__":
    sys.exit(main())
