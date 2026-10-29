#!/usr/bin/env python3
"""The bookkeeping role's derivations: which thirds run, the artifact's form, and the store.

`session.parts` (§ 23), the save artifact and § 25's memory store are one role's
facts with more than one reader -- the role writes and a later pass reads -- so
the derivation lives here rather than in the role's own text. ⛔ **That is § 10's
rule for a branch name, one role over**: a form copied into a role's text is a
form allowed to disagree with the thing that holds a written artifact to it, and
the direction nothing reports is the reader accepting an artifact that is missing
what a resume needs.

⛔ **It states no rule of its own.** Which thirds there are, the order they run
in, when a save is owed and what the artifact is for are `../config/schema.md`
§ 23's; where the memory store is, which working directory may write it and what
an entry has to carry are § 25's. Both are read through the shared reader. What
this module owns is what none of its readers should perform twice:

  * **The thirds this project runs**, in the procedure's order rather than the
    order a configuration happens to list them in, each with what it reads and
    whether that mechanism is there at all.
  * **The form** of a save artifact: the fields a resuming pass needs, and the
    boundary vocabulary.
  * **The reading back** of a written artifact against that form -- which is both
    how the writing role checks what it wrote and how a resuming pass reads it,
    the same answer serving both because they are the same question asked from
    two sides.
  * **The memory store's location and the write decision** (§ 25): the path a
    project pinned or the answer that there is none to compose, and whether the
    working directory the session is standing in may write it -- *write*,
    *refuse*, or an answer nobody could establish, which is three values and
    never two.
  * **The memory entry's form, and its admission**: a fact carries where it came
    from and what it rests on, held at write time, because a store already
    carrying an unprovenanced fact cannot be read back into one that does not.
  * **The reading of one entry out of a store whose admission never ran** (§ 25):
    what the entry states, what it *reads as* where it states nothing, and which
    of three standings the fact is reported under -- current, **stale**, or
    unchecked.
  * **The locked append to the index**, which is the one file two sessions
    contend on.

⛔ **The fields are keys and never headings, and the prose under them is the
project's own.** § 8 fixes the language an artifact is written in per project, so
a form demanding English headings would be this module shipping one project's
vocabulary to every project -- the thing the surface refuses twice over. A key is
not prose: the value beside it is, in whatever language the project states.

⚠️ **What the round trip proves and what it does not.** The suite below writes a
form, reads it back and asserts every field is recovered, which is the decidable
end of *resumable from the artifact alone*. What it cannot establish is whether
the prose a role wrote into those fields is enough for a person or a later
session to continue -- that is the *quoting* kind of check, green on prose
reworded into its opposite. ⛔ **So the residue is stated rather than implied**:
this holds that the form carries every field a resume asks for and that a written
artifact answers all of them, and the sufficiency of what is written in them is
read rather than enforced.

Usage:
    save.py [--skills-root DIR]        the thirds this project runs, in order --
                                       and, where the memory third is one of
                                       them, § 25's store and the write decision
    save.py form                       the fields a save artifact carries
    save.py check --file PATH          hold a written artifact to the form, and
                                       report what a resuming pass reads out of it
    save.py entry                      the fields a memory entry carries (§ 25)
    save.py recall --file PATH [--premise holds|broken|unchecked]
                                       read one written entry -- in the entry form
                                       or in the shape a store whose admission
                                       never ran holds -- and report what it
                                       states, what it reads as, and the standing
                                       the reader's own answer about its premise
                                       puts it under
    save.py memory [--skills-root DIR] [--standing-in DIR]
                                       where the store is, whether that directory
                                       may write it, and what the carrier leaves
                                       open
    save.py remember [--skills-root DIR] [--standing-in DIR]
                     --entry PATH --name FILE --line TEXT
                                       admit one entry, place it in the store
                                       under that name, and append its index line
                                       under a lock

Exit status, and ⛔ **four values rather than two**: 0 the artifact or entry
holds, the write happened, or the report was produced, 1 it does not hold or the
write was refused, 2 something that had to be read could not be -- the
configuration, the artifact's own file, or the entry's -- and 3 there is nothing
to answer about, this project mapping no bookkeeping role or stating no
configuration at all. ⚠️ **2 and 1 are apart on purpose**: an artifact whose file
could not be opened has not failed the form, and a role told it failed would
rewrite a file that is already right. ⚠️ The last is § 11's rule at a command
line: *no answer* collapsed into 0 reads as an artifact that passed, and into 1
as a role whose every save is wrong.

⚠️ **`memory` is the one subcommand whose non-zero status is not a fault.** A
refusal to write from a tree is that command working, so it exits 0 and says so;
the 1 is reserved for the decision nobody could establish, which is § 11's rule
again one command over.

⚠️ **`recall`'s 1 covers two unlike things, and `standing` is which.** An entry
that fails the form is a file to rewrite; a fact whose premise the reader reports
broken is a **stale** fact to re-measure or delete, and that one comes back with
`holds` **true** and no problems at all -- the entry being fine and the fact not.
⛔ So the 1 there reads *not a fact to use as current* rather than *it does not
hold*, and it is a 1 rather than a 0 because a stale fact sharing a current one's
status is the restatement § 25's standing rule exists against, read off the
status alone.
"""

from __future__ import annotations

import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config  # noqa: E402 -- the one reader, not a second parser

# --- the thirds ------------------------------------------------------------
#
# ⛔ The order is procedure (§ 23) and the vocabulary is the surface's, so this
# table carries the order and reads the names out of the reader rather than
# listing them: a fourth third added to the surface arrives here unplaced, which
# `thirds` below reports rather than dropping.
#
# ⚠️ What each third reads is named and not resolved. Whether the port can write,
# whether a status's writer is this role's, and whether a store exists are each
# answered where they are configured, and a second answer here would be the
# duplication the whole toolkit exists to delete.
ORDER = ["tracker", "memory", "commit"]

READS = {
    "tracker": (
        "the tracker port's writes (§ 3) and the status writer model (§ 4.2) -- "
        "and no status whose writer is somebody else"
    ),
    "memory": (
        "the store § 25's `memory` block states, and which working directory that "
        "block lets a save write it from"
    ),
    "commit": "this role's own `commit.staging` entry (§ 6)",
}

# The third whose mechanism is a block of the project's rather than a capability
# of something else, and the key that carries it. ⛔ Availability is asked of the
# configuration rather than written down here: before § 25 this third had no
# store at all and was listed as unavailable unconditionally, and what replaced
# that is a question -- is the block there -- whose answer can be no again. ⚠️ It
# can be no on a *correct* project: § 1 resolves a work tree against its own
# surface, so a tree cut before § 25 states no block and the reader that ruled it
# marked none, which is the direction that fails safe.
MEMORY_THIRD = "memory"
MEMORY_KEY = "memory"


def _place(stated: list, carried=lambda name: True) -> list[dict]:
    """The stated thirds in the procedure's order, whatever order they arrived in.

    ⛔ A seam of its own, so the ordering is asserted against a list written
    backwards rather than against a fixture that happens to be in the right
    order already -- an assertion written in the order it expects asserts the
    expectation and not the code.
    """
    placed = [name for name in ORDER if name in stated]
    # Anything the surface states that this module has no place for is reported
    # rather than lost: a third running in an order nothing decided is worse than
    # one reported as unplaced.
    unplaced = [name for name in stated if name not in ORDER]
    return [
        {
            "part": name,
            "reads": READS.get(name, "nothing this module can name"),
            "available": carried(name),
            "placed": name in ORDER,
        }
        for name in placed + unplaced
    ]


def thirds(configuration: config.Config) -> list[dict]:
    """Which thirds run here, in the procedure's order, each with its state."""
    stated = configuration.get("session.parts")

    def carried(name: str) -> bool:
        # ⛔ One third's availability is a question and the other two's is not:
        # the tracker third's mechanism is the port's own answer and the commit
        # third's is held by the reader refusing a mapped role with no staging,
        # so neither is answered a second time here (§ 23). The memory third's is
        # a block of the project's, and whether that block is there is a fact
        # this module can read.
        if name != MEMORY_THIRD:
            return True
        return configuration.get(f"{MEMORY_KEY}.carrier") is not None

    # ⛔ A value the reader has already refused cannot arrive here, and the
    # normalisation is still written: a string handed to `_place` is iterated
    # character by character, so the one shape that would read as a list of
    # thirds and be none is the one left out rather than guessed at.
    return _place(list(stated) if isinstance(stated, list) else [], carried)


# --- the form --------------------------------------------------------------
#
# ⛔ Every field is required, and the list is what *resumable from the artifact
# alone* means in fields: a pass that reads this file and nothing else can say
# which item it is on, where the work is, what the item asks for and how much of
# that is answered, what is in the tree that is not in a commit, and what the
# last pass asked somebody. A field a project may omit would be a field a resume
# cannot rely on, which is the whole of what the artifact is for.
#
# ⚠️ `boundary` is first because it is the field that changes what a reader does
# with the rest: a save taken mid-item and one taken after the work was done
# license different next steps, and without it the two are indistinguishable.
FIELDS = [
    ("boundary", "which boundary this save was taken at"),
    ("item", "the work item, by identifier and title"),
    ("code_root", "the named code root the work is in (§ 1)"),
    ("branch", "the branch the claim is published on (§ 10)"),
    ("tree", "the tree the work happens in, or that there is none"),
    ("acceptance", "the item's stated condition, and which parts of it are answered"),
    ("committed", "what is committed, and what is in the tree and is not"),
    ("asked", "every question this pass asked and its answer, or that it is open"),
]

# The names this form gives § 23's four occasions, as the field's closed set. A
# save taken at a boundary this does not name is an artifact whose reader cannot
# tell what it is holding, so the value is refused rather than passed through.
#
# ⛔ The spellings are **this form's** and the surface states none of them, which
# is § 23's rule that the form is the carrier's rather than an omission. So a
# refusal here names the form and never the section: a message citing § 23 for
# these four tokens sends a person to a passage that does not carry them, which
# is worse than carrying the set here.
#
# ⚠️ What that leaves open is stated rather than closed: § 23 states *when* a
# save is owed in prose, and nothing holds these four names to that prose. A
# fifth occasion there and this set fall out of step with no check reporting it
# -- the same limit `READS` above carries, and the reason neither is written as
# though the surface decided it.
BOUNDARIES = ["handoff", "compaction", "session_end", "asked"]

# The fields of this form whose value comes from a set, and what a reader loses
# where one is outside it. ⛔ Keyed by field so `_held` performs it for either
# form: a closed set is a property of a field rather than of a form, and a
# function taking one set for one named field would hold the other form's by
# nothing.
CLOSED = {
    "boundary": (
        BOUNDARIES,
        "A boundary a reader cannot place is a save it cannot tell mid-item from "
        "finished",
    ),
}


def form() -> dict:
    """The fields a save artifact carries, and the boundary vocabulary."""
    return {
        "fields": [{"field": name, "carries": what} for name, what in FIELDS],
        "boundary": list(BOUNDARIES),
        "shape": (
            "one block of `field: value` pairs, the keys as spelled here and the "
            "values in the project's own language (§ 8)"
        ),
    }


def _held(
    text: str, fields: list, closed: dict, what: str
) -> tuple[dict | None, list[str]]:
    """(the fields a reader recovers, the problems holding the text to the form).

    ⛔ Parsed through the one reader's YAML rather than a grammar of its own: a
    written form is a configuration-shaped file, and a second parser for one
    format is the defect this module is an instance of refusing.

    ⛔ **One function for both of this module's forms**, and that is the rule
    rather than a convenience: the save artifact and § 25's memory entry are each
    a block of keys whose values a later pass reads, so a second copy of these
    arms would be a copy allowed to hold one of them to less than the other --
    and the half that drifted would be the newer one, with every assertion green.
    `closed` is the only thing that differs between them: the fields whose value
    comes from a set the form states.
    """
    try:
        document = config._load_yaml(text, what)
    except config.ConfigError as exc:
        return None, [str(exc)]
    # ⛔ An empty file is named as empty rather than by the type its parse
    # happened to produce: it is the commonest way this goes wrong — the role
    # created the file and wrote nothing into it — and a reader quoting a
    # language's type name at a person has reported the implementation instead
    # of the problem.
    if document is None:
        return None, [
            f"{what} is empty, so none of the form's fields can be read out "
            "of it: an empty file is a save that did not happen"
        ]
    if not isinstance(document, dict):
        return None, [
            f"{what} is not a block of fields, so none of the form's fields "
            "can be read out of it"
        ]

    problems = []
    known = {name for name, _ in fields}
    for name, carries in fields:
        if name not in document:
            problems.append(f"`{name}` is missing, and it carries {carries}")
            continue
        value = document[name]
        if value is None or (isinstance(value, str) and not value.strip()):
            problems.append(
                f"`{name}` is written and empty, which reads as answered and is "
                f"not: it carries {carries}"
            )
            continue
        # ⛔ A structure is not an answer, and it passes every other arm here. A
        # field carries prose a later pass reads, so a mapping or a list under
        # one is a field a resume cannot read while the form reports it
        # answered. ⚠️ A number is accepted: an identifier is one.
        if isinstance(value, (dict, list)):
            problems.append(
                f"`{name}` carries a {'block' if isinstance(value, dict) else 'list'} "
                f"rather than an answer, so nothing reads what it carries: it "
                f"carries {carries}"
            )
            continue
        # ⛔ And a boolean is not an answer either, which the arms above all let
        # through: `false` is neither empty nor a container, so a field carrying
        # it reported as answered. ⚠️ A number is accepted on purpose — an
        # identifier is one — and the limit that leaves is stated rather than
        # closed: a field carrying `0` passes, because refusing it would refuse
        # an item numbered zero.
        if isinstance(value, bool):
            problems.append(
                f"`{name}` carries {str(value).lower()} rather than an answer, so "
                f"nothing reads what it carries: it carries {carries}"
            )
    # ⛔ Sorted by the key's text and not by the key, because a key YAML read as
    # a number sorts against a string and raises -- out of the one function whose
    # contract is to return problems rather than to fail.
    for name in sorted((key for key in document if key not in known), key=str):
        problems.append(
            f"`{name}` is not a field of the form, so whatever it carries is read "
            "by nothing. The form is this module's and not the writing role's"
        )
    for name, (allowed, why) in sorted(closed.items()):
        value = document.get(name)
        if value is not None and value not in allowed:
            problems.append(
                f"`{name}` is {value!r}; the form states {' | '.join(allowed)}. {why}"
            )
    recovered = {name: document.get(name) for name, _ in fields}
    return recovered, problems


def read(text: str) -> tuple[dict | None, list[str]]:
    """(the fields a resuming pass reads, the problems holding it to the form)."""
    return _held(text, FIELDS, CLOSED, "the save artifact")


# --- the memory store (§ 25) -----------------------------------------------
#
# ⛔ Three things the role must not perform for itself, for the reason the form
# above is here: each has more than one reader -- the bookkeeping role writes the
# store and the restoring role reads it -- and each is a question whose wrong
# answer is silent.
#
#   * **Where the store is**, which is a path the project states or an answer
#     that there is no path to compose.
#   * **Whether the working directory the session is standing in may write it**,
#     which is the only arm that turns § 25's measured hazard into something a
#     role can act on rather than a caution it has to remember.
#   * **What an entry carries**, which is the write-time admission § 25 states:
#     a fact with no provenance and no premise is a fact a later pass can only
#     restate.

# ⛔ The two readings an entry's provenance may carry, and the whole point of the
# set: a fact this pass observed and a fact it read somewhere and passed on are
# different evidence, and a store that renders them identically is a store where
# the second becomes the first by being read twice (§ 25).
PROVENANCE = ["measured", "repeated"]

# ⛔ The fields, by the same rule the artifact's are: every one required, and the
# list is what *checkable rather than restatable* means in fields. A reader with
# these four can say what the fact is, how it came to be believed, what it was
# established from, and what would have to change for it to stop being true --
# and § 24's obligation to check a recalled fact is takeable only with the last
# of those.
#
# ⚠️ `asof` is deliberately not among them, and the omission is stated rather
# than silent: a date says when the fact was written and not whether its premise
# still holds, so a form carrying one would answer staleness with a number that
# reads like an answer. What `premise` asks for is the check itself.
ENTRY_FIELDS = [
    ("fact", "the fact itself, in the project's own language (§ 8)"),
    ("provenance", "how it came to be believed -- " + " | ".join(PROVENANCE)),
    ("source", "what it was established from: the command, the file, the person"),
    ("premise", "what would have to change for it to stop being true"),
]

ENTRY_CLOSED = {
    "provenance": (
        PROVENANCE,
        "A fact whose provenance a reader cannot place is a fact that becomes "
        "measured by being read twice",
    ),
}


def entry_form() -> dict:
    """The fields a memory entry carries, and the provenance vocabulary."""
    return {
        "fields": [{"field": name, "carries": what} for name, what in ENTRY_FIELDS],
        "provenance": list(PROVENANCE),
        "shape": (
            "one block of `field: value` pairs, the keys as spelled here and the "
            "values in the project's own language (§ 8)"
        ),
        "admission": (
            "an entry missing any of these is refused at write time rather than "
            "filtered at read time: a store already carrying an unprovenanced "
            "fact cannot be read back into one that does not (§ 25)"
        ),
    }


def read_entry(text: str) -> tuple[dict | None, list[str]]:
    """(what a reader recovers from an entry, the problems holding it to the form)."""
    return _held(text, ENTRY_FIELDS, ENTRY_CLOSED, "the memory entry")


# --- reading one entry out of a store whose admission never ran (§ 25) ------
#
# ⛔ The admission above runs at write time and is reachable only under a pinned
# store: under `derived` the command that performs it composes no path and writes
# nothing, so **no entry in such a store has been through it** and none of them
# carries the two fields the rule requires. That is the third thing that carrier
# leaves open, and this is the half that makes the store it leaves readable at
# all.
#
# ⛔ **Read rather than refused, and each rule failing in the direction that
# under-claims.** A reading that refuses the whole entry tells its reader nothing
# about what they are holding; one that recovers the fact and names the absent
# fields leaves them with the fact and with the knowledge that it is neither
# provenanced nor checkable.

# What a fact states nothing about its provenance reads as. ⛔ The whole of the
# failing-safe direction, in one name: `measured` is a value an entry has to
# state, and a store where its absence read as the better of the two is a store
# where a repeated fact becomes a measured one by being written without a field.
UNSTATED_READS_AS = "repeated"

# The standing a recalled fact is reported under, and ⛔ three rather than two.
# ⚠️ The spellings are **this module's** and the surface states none of them,
# which is § 25's rule that they are the carrier's -- the same division
# `BOUNDARIES` above carries, with the same limit: a standing added here and
# § 25's prose fall out of step with no check reporting it.
CURRENT, STALE, UNCHECKED = "current", "stale", "unchecked"
STANDINGS = [CURRENT, STALE, UNCHECKED]

# What a reader may answer about the premise, and what each answer puts the fact
# under. ⛔ The answer comes from the reader and never from the entry: the premise
# is read against the tree, which is the one part of this no command can take.
PREMISE_ANSWERS = {"holds": CURRENT, "broken": STALE, "unchecked": UNCHECKED}

# The fence a store's own entries are wrapped in where they carry one -- a
# leading YAML document, then prose. ⚠️ Named as a shape this module **reads**
# and never as one it writes: what `remember` admits is the entry form, and this
# is how the store a derived carrier hands over actually holds a fact.
FENCE = "---"


def _fenced(text: str) -> tuple[dict | None, str] | None:
    """(the leading document's keys, the prose after it), or None if unfenced.

    ⛔ The keys come back and are **not mined for the form's fields**: a mapping
    invented here would be the procedure guessing another tool's vocabulary, and
    the guess actually on offer in the measured store is a subject label, which
    is not an evidence class (§ 25). They are returned so a reader can be told
    what shape the file is in, not so a field can be taken out of them.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != FENCE:
        return None
    for at in range(1, len(lines)):
        if lines[at].strip() == FENCE:
            head = "\n".join(lines[1:at])
            try:
                keys = config._load_yaml(head, "the entry's leading document")
            except config.ConfigError:
                keys = None
            return (keys if isinstance(keys, dict) else None,
                    "\n".join(lines[at + 1:]))
    return None


def recalled(text: str, premise: str = "unchecked") -> tuple[int, dict]:
    """(status, what a reader gets from one entry) -- § 25's read-time half.

    ⛔ **Two answers and not one**: what the entry *states*, and what it *reads
    as*. An entry that states no provenance reads as repeated, which is the only
    direction that does not turn a passed-on fact into a measured one by leaving
    a field out.

    ⛔ **And the standing is reported rather than implied.** A premise the reader
    checked and found broken makes the fact **stale**, which is § 24's rule given
    somewhere to land; a premise nothing checked leaves it unchecked; and
    *current* over an entry that states no premise is **refused**, that being the
    restatement the rule is against arriving through this very command.

    ⚠️ Two fields of what comes back are narrower than they read, stated here
    rather than left to be inferred: `shape` is the form the entry was **read
    against** and not a claim about what the file is, and `holds` is about that
    form alone -- a refusal of the *reader's own answer* about the premise leaves
    it true, the entry being fine and the answer not.
    """
    recovered, problems = read_entry(text)
    shape = "the entry form"
    unstated: list[str] = []
    report: list[str] = []
    if problems:
        # ⛔ The store's own shape, tried only once the form has failed -- so an
        # entry that holds the form is never read through the lenient arm, and
        # the admission's own refusals keep every bit of their reach.
        fenced = _fenced(text)
        if fenced is None:
            return 1, {
                "shape": shape,
                "holds": False,
                "problems": problems,
                "read": recovered,
                # ⚠️ Sorted, like the fenced arm's: one reader meets both, and a
                # field list whose order depends on which arm produced it is a
                # list a caller cannot compare.
                "unstated": sorted(name for name, _ in ENTRY_FIELDS),
                "reads_as": UNSTATED_READS_AS,
                "standing": UNCHECKED,
                "report": [
                    "Read against the entry form, which it does not hold, and it "
                    "is not in the shape a store holds either -- so there is "
                    "nothing to read a fact out of at all (§ 25)."
                ],
            }
        keys, body = fenced
        shape = "the store's own"
        recovered = {name: None for name, _ in ENTRY_FIELDS}
        recovered["fact"] = body.strip() or None
        unstated = sorted(name for name, _ in ENTRY_FIELDS if recovered[name] is None)
        problems = []
        report.append(
            f"This entry is in the store's own shape rather than the entry form, "
            f"so it never went through § 25's admission: the fields it does not "
            f"carry are {', '.join('`' + name + '`' for name in unstated)}, and "
            "⛔ no key of its leading document is read as one of them -- the one "
            "on offer is a subject label and not an evidence class."
        )
        if keys is None:
            report.append(
                "Its leading document could not be read as a block of keys, which "
                "changes nothing about the fields above: none of them would have "
                "been taken from it either way (§ 25)."
            )
        # ⛔ A fact is the one thing a reading cannot do without, so an entry in
        # this shape with nothing under its fence is refused rather than handed
        # back as a fact that is empty.
        if recovered["fact"] is None:
            return 1, {
                "shape": shape,
                "holds": False,
                "problems": [
                    "the entry carries nothing after its leading document, so there "
                    "is no fact to recall out of it at all (§ 25)"
                ],
                "read": recovered,
                "unstated": unstated,
                "reads_as": UNSTATED_READS_AS,
                "standing": UNCHECKED,
                "report": report,
            }

    stated = (recovered or {}).get("provenance")
    reads_as = stated if stated in PROVENANCE else UNSTATED_READS_AS
    if stated not in PROVENANCE:
        report.append(
            f"`provenance` is unstated, so this fact reads as **{UNSTATED_READS_AS}** "
            f"rather than as measured: ⛔ `measured` is a value an entry has to "
            "state, and its absence is not the permissive reading of it (§ 25)."
        )

    # ⛔ The reader's answer, held to the three words before it is acted on: a
    # fourth would otherwise arrive as a standing nothing names.
    if premise not in PREMISE_ANSWERS:
        return 1, {
            "shape": shape,
            "holds": True,
            "problems": [
                f"the premise was answered {premise!r}; the three a reader may give "
                f"are {' | '.join(sorted(PREMISE_ANSWERS))} (§ 25)"
            ],
            "read": recovered,
            "unstated": unstated,
            "reads_as": reads_as,
            "standing": UNCHECKED,
            "report": report,
        }
    standing = PREMISE_ANSWERS[premise]
    # ⛔ *Current* over an entry stating no premise is refused, which is the arm
    # the whole standing exists for: there was nothing to check, so a reader
    # answering that it holds has asserted the fact rather than checked it.
    #
    # ⛔ **Absent and never falsy**, which is the one test that agrees with the
    # form above. `_held` accepts `premise: 0` -- a number being how an identifier
    # arrives, so the arm that refuses a boolean lets a zero through -- and a
    # truthiness test here would then refuse it as *stating none*, which is a
    # refusal whose own message is false about the entry. Found by review on this
    # change; the direction was safe and the sentence was not.
    if standing == CURRENT and (recovered or {}).get("premise") is None:
        return 1, {
            "shape": shape,
            "holds": True,
            "problems": [
                "the premise was answered as holding and the entry states none, so "
                "nothing was checked: ⛔ a fact reported current on an unstated "
                "premise is the restatement § 24 refuses, arriving through the "
                "command written to prevent it (§ 25)"
            ],
            "read": recovered,
            "unstated": unstated,
            "reads_as": reads_as,
            "standing": UNCHECKED,
            "report": report,
        }
    if standing == CURRENT:
        report.append(
            "The premise above was checked by whoever ran this and reported as "
            "holding, so the fact is **current** -- ⛔ on that reading and not on "
            "this command's, which checks nothing (§ 24)."
        )
    elif standing == STALE:
        report.append(
            "The premise above was checked and does not hold, so the fact is "
            "**stale**: ⛔ reported as stale and never restated as current, and "
            "the entry is re-measured or deleted rather than read again (§ 24, "
            "§ 25)."
        )
    else:
        report.append(
            "The premise has not been checked by this command and cannot be: it is "
            "read against the tree by whoever reads the fact. ⛔ Report the fact "
            "with its premise, or report it unchecked -- never as current (§ 24, "
            "§ 25)."
        )
    return (1 if standing == STALE else 0), {
        "shape": shape,
        "holds": True,
        "problems": [],
        "read": recovered,
        "unstated": unstated,
        "reads_as": reads_as,
        "standing": standing,
        "report": report,
    }


def _git(where: str, *args: str) -> str | None:
    """One read-only git answer from `where`, or None where git cannot give one."""
    import subprocess  # noqa: PLC0415 -- the only arm that needs a process

    try:
        done = subprocess.run(
            ["git", "-C", where, *args],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def standing_in_a_tree(where: str) -> tuple[bool | None, str | None]:
    """(whether `where` is a linked worktree, the main checkout's path).

    ⛔ Asked of git and never of the configuration, which is the whole substance
    of this function. § 1 resolves a work tree against that tree's own files, so
    a session standing in a tree resolves the *tree* as its skills root -- which
    means comparing a working directory against the resolved root answers `yes,
    this is the checkout` in exactly the case § 25 is written about.

    ⚠️ `None` where git could not answer, and it is returned rather than
    defaulted: a working directory nothing could place is reported unplaced, and
    the permissive reading of it is the one that writes a tree's own store
    (§ 11's rule that a report names what it could not establish).
    """
    own = _git(where, "rev-parse", "--path-format=absolute", "--git-dir")
    shared = _git(where, "rev-parse", "--path-format=absolute", "--git-common-dir")
    if not own or not shared:
        return None, None
    checkout = os.path.dirname(os.path.normpath(shared))
    return os.path.normpath(own) != os.path.normpath(shared), checkout


def memory(configuration: config.Config, standing_in: str) -> dict:
    """§ 25's store, the write decision for one working directory, and what is open.

    ⛔ The decision is three-valued and never two: write, refuse, and *could not
    be established*. The third is the one a report collapses into a permission by
    accident, and collapsing it writes a tree's own store and says it succeeded.
    """
    carrier = configuration.get(f"{MEMORY_KEY}.carrier")
    if carrier is None:
        return {
            "carried": False,
            "carrier": None,
            "may_write": None,
            "store": None,
            "index": None,
            "unclosed": [],
            "report": [
                "No `memory` block is carried, so there is no store for the memory "
                "third to write and this pass composes no path (§ 25). ⛔ Not that "
                "the third ran: a surface older than § 25 marks no such block, so "
                "a tree cut before it reads as a project that states none."
            ],
        }
    # ⛔ The project's stated absence, answered before anything below reads a key
    # that carrier refuses. ⚠️ Found by review on this change, reproduced: without
    # this arm a project keeping no memory fell through to the `derived` branch
    # and was told *the store is the harness's own* -- naming a carrier it does
    # not state, reporting two hazards it does not have, and handing back a write
    # decision about a store that does not exist. ⛔ Reachable rather than
    # theoretical: the restoring role runs whatever `session.parts` says, so it
    # asks this question on exactly those projects.
    if carrier == "none":
        reason = configuration.get(f"{MEMORY_KEY}.absent_reason")
        return {
            "carried": False,
            "carrier": carrier,
            "may_write": None,
            "store": None,
            "index": None,
            "unclosed": [],
            "report": [
                "No memory store is carried (`memory.carrier: none`), so the memory "
                "third does not run and there is nothing for a restoring pass to "
                f"check a recalled fact against: {' '.join(str(reason).split())} "
                "⛔ Not a store that is empty, and not a write refused: there is no "
                "store (§ 25)."
            ],
        }
    write_from = configuration.get(f"{MEMORY_KEY}.write_from")
    in_a_tree, checkout = standing_in_a_tree(standing_in)

    out = {
        "carried": True,
        "carrier": carrier,
        "write_from": write_from,
        "standing_in": os.path.abspath(standing_in),
        "in_a_tree": in_a_tree,
        "main_checkout": checkout,
        "store": None,
        "index": None,
        "unclosed": [],
        "report": [],
    }

    if carrier == "path":
        # ⚠️ Expanded here and not by the reader, which is § 11's rule for the
        # artifact store's own path one facet over: the reader keeps what a
        # project wrote, and the role's command is what resolves `~` and a shell
        # variable in it. Relative is relative to the skills root, like every
        # path on this surface (§ 1).
        stated = configuration.get(f"{MEMORY_KEY}.store")
        named = configuration.get(f"{MEMORY_KEY}.index")
        # ⛔ Unanswered rather than stringified, which is what the first form of
        # this did: `str(None)` is a path called `None`, so a configuration this
        # reader had not refused -- one held to a surface whose conditional marker
        # predates these keys (§ 1) -- would have had its store composed as a
        # directory named after a Python literal, and written to. Found by review.
        if not isinstance(stated, str) or not isinstance(named, str):
            out["report"].append(
                "`memory.carrier: path` with no `store` and `index` to resolve, so "
                "where the store is could not be established and this pass "
                "composes no path (§ 25). ⛔ Reported unanswered rather than "
                "guessed: the surface requires both keys under this carrier, so "
                "meeting this means the configuration was held to a surface that "
                "does not."
            )
            out["may_write"] = None
            return out
        resolved = os.path.expanduser(os.path.expandvars(stated))
        if not os.path.isabs(resolved):
            resolved = os.path.join(os.path.abspath(configuration.skills_root), resolved)
        out["store"] = os.path.normpath(resolved)
        out["index"] = os.path.join(out["store"], named)
        out["unclosed"].append(
            "The store the project pinned is the store the procedure writes, and "
            "nothing here holds it to being the store the harness writes: two of "
            "them held apart by nobody is the same defect one level out (§ 25)."
        )
    else:
        out["unclosed"] += [
            "The index two sessions contend on cannot be appended under a lock "
            "from here, the store's own directory being what this carrier must "
            "not guess at -- so concurrent entries can lose each other (§ 25).",
            "A checkout that is moved or renamed derives a different store and "
            "orphans the old one, with nothing said (§ 25).",
            # ⛔ The third, and it is a third rather than a restatement of the two
            # above: those lose a fact or orphan it, while this one leaves every
            # fact in the store unprovenanced and uncheckable *while reading
            # exactly like a fact that carries both*. ⚠️ Measured on this
            # repository, which is the only project running the memory third --
            # the admission's own command writes nothing under this carrier, so
            # no entry in the store has been through it.
            "The write-time admission is unreachable here, there being no store "
            "for `remember` to place a fact in -- so no entry carries a "
            "provenance or a premise, every recalled fact reads as "
            f"**{UNSTATED_READS_AS}** and is reported unchecked, and § 24's check "
            "is not takeable through the entry at all (§ 25).",
        ]
        out["report"].append(
            "The store is the harness's own (`memory.carrier: derived`), so this "
            "pass composes no path to it and the third is run through whatever "
            "the harness hands the session (§ 25)."
        )

    # ⛔ Held to the two words before any branch below quotes one of them. ⚠️ Each
    # of those branches names `main_tree` in its message, so an absent key -- § 1's
    # work-tree case again, a configuration held to a surface whose conditional
    # marker predates this key -- would have had the decision reported under a
    # value the project never stated. Found by review on this change.
    if write_from not in ("main_tree", "any_tree"):
        out["report"].append(
            f"`memory.write_from` is {write_from!r} rather than one of the two "
            "words § 25 states, so which working directory may refresh memory "
            "could not be established. ⛔ Reported unanswered rather than read as "
            "either: the permissive reading of it writes a tree's own store."
        )
        out["may_write"] = None
        return out
    if write_from == "any_tree":
        out["may_write"] = True
        out["report"].append(
            "`memory.write_from: any_tree`, so the memory third runs from this "
            "working directory and writes the configured store rather than the "
            "one the directory would derive (§ 25)."
        )
    elif in_a_tree is None:
        # ⛔ Unanswered, and never read as the checkout. The permissive reading
        # here is the one that writes a tree's own store and reports success.
        out["may_write"] = None
        out["report"].append(
            "`memory.write_from: main_tree`, and whether this working directory "
            "is a linked tree or the checkout could not be established -- git "
            "answered neither `--git-dir` nor `--git-common-dir`. ⛔ Reported "
            "unanswered rather than as the checkout (§ 11): the permissive "
            "reading is the one that writes a tree's own store."
        )
    elif in_a_tree:
        out["may_write"] = False
        out["report"].append(
            "`memory.write_from: main_tree` and this working directory is a "
            "linked tree, so the memory third **refuses** here and the refusal is "
            f"named: the checkout it would run from is {checkout!r} (§ 25)."
        )
    else:
        out["may_write"] = True
        out["report"].append(
            "`memory.write_from: main_tree` and this working directory is the "
            "checkout, so the memory third runs here (§ 25)."
        )
    return out


def _contained(name: str) -> str | None:
    """The problem with `name` as a file inside the store, or None.

    ⛔ The role hands a name over and **this** places it, which is the whole
    reason the command exists -- so a name that is a path would be the role
    writing wherever it liked through the one call written to stop that (§ 25).
    """
    if not name or not name.strip():
        return (
            "the fact's own file is unnamed, so there is nothing for the store to "
            "hold it under (§ 25)"
        )
    if os.path.isabs(name) or os.path.basename(name) != name or name in (".", ".."):
        return (
            f"the fact's file name is {name!r}, which is a path rather than a name "
            "inside the store: this command places the file, so a name that "
            "reaches out of the store writes where nothing reads and where § 25's "
            "rules about the store do not hold"
        )
    return None


def remember(
    configuration: config.Config,
    standing_in: str,
    entry: str,
    name: str,
    line: str,
) -> tuple[int, dict]:
    """Admit one entry, place it in the store, and append its index line under a lock.

    ⛔ **The admission runs before anything is written**, which is § 25's whole
    position on this: a store that accepts an unprovenanced fact cannot be read
    back into one that does not, so the one place the rule buys anything is here.

    ⛔ **The fact's file is placed by this command and never by the role**, so no
    role ever composes a path inside the store -- which is the same division
    `memory` above draws for the store itself.

    ⛔ **And the index is appended under a lock rather than read, edited and
    written back.** The per-fact files are safe under parallel trees, two sessions
    rarely writing the same fact; the index is the file every session reads, and
    two concurrent rewrites of it lose each other.
    """
    where = memory(configuration, standing_in)
    if where["may_write"] is not True:
        return 1, {
            "wrote": False,
            "problems": where["report"],
            "where": where,
        }
    if where["carrier"] != "path":
        return 1, {
            "wrote": False,
            "problems": [
                "The store is the harness's own (`memory.carrier: derived`), so "
                "there is no directory for this command to write a fact into and "
                "no index for it to lock: the third is run through the harness "
                "and ⛔ the contention on its index stays open (§ 25)."
            ],
            "where": where,
        }
    try:
        with open(entry, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        return 2, {"wrote": False, "problems": [str(exc)], "where": where}
    recovered, problems = read_entry(text)
    if problems:
        return 1, {"wrote": False, "problems": problems, "where": where}
    uncontained = _contained(name)
    if uncontained:
        return 1, {"wrote": False, "problems": [uncontained], "where": where}
    if not line.strip():
        return 1, {
            "wrote": False,
            "problems": [
                "the index line is blank, so the entry would be written into the "
                "store and reachable from nothing that reads it (§ 25)"
            ],
            "where": where,
        }
    placed = os.path.join(where["store"], name)
    # ⛔ The fact's file first and the index line second, which is ordering rather
    # than arrangement: an index line pointing at a file that is not there yet is
    # a store a concurrent reader finds broken, while a file no line points at is
    # a store that is merely missing one entry.
    #
    # ⛔ And the write is reported rather than raised. This function's contract is
    # to return a status and what went wrong, and a store that cannot be created
    # or a name that is already a directory are both ordinary states of somebody
    # else's filesystem -- so a traceback here would be the one failure mode the
    # whole report exists against, out of the one function whose promise is to
    # name the problem. ⚠️ The index is untouched on either, so a refusal leaves
    # no line pointing at a fact nobody wrote. Found by review on this change.
    try:
        os.makedirs(where["store"], exist_ok=True)
        with open(placed, "w", encoding="utf-8") as handle:
            handle.write(text)
    except OSError as exc:
        return 1, {
            "wrote": False,
            "problems": [
                f"the store would not take the fact: {exc}. ⛔ The index was left "
                "alone, so nothing in it points at a fact that was never written "
                "(§ 25)"
            ],
            "where": where,
        }
    _append_under_lock(where["index"], line.rstrip("\n") + "\n")
    return 0, {
        "wrote": True,
        "store": where["store"],
        "index": where["index"],
        "fact": placed,
        "read": recovered,
        "unclosed": where["unclosed"],
        "where": where,
    }


def _append_under_lock(path: str, line: str) -> None:
    """Append one line to `path`, holding an exclusive lock across the write.

    ⛔ `O_APPEND` alone is not what this rests on and the lock is not decoration:
    the failure § 25 names is a *read, edit, write back* of the whole index, and
    what the lock buys is that a reader taking the file between two sessions'
    writes cannot see it half-written either. ⚠️ Where the platform has no
    `fcntl` the append still happens and the lock does not, which is stated here
    rather than discovered: every runner this is held on is POSIX.
    """
    try:
        import fcntl  # noqa: PLC0415 -- POSIX only, and the fallback is the append
    except ImportError:
        fcntl = None
    handle = open(path, "a", encoding="utf-8")
    try:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX)
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    finally:
        if fcntl is not None:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        handle.close()


# --- the self-test ---------------------------------------------------------


def _an_artifact(**overrides) -> str:
    """A complete artifact, to break in a stated way."""
    written = {name: f"what {name} carries" for name, _ in FIELDS}
    written["boundary"] = "compaction"
    written.update(overrides)
    return "\n".join(
        f"{name}: {value}" for name, value in written.items() if value is not None
    ) + "\n"


def _without(field: str) -> str:
    written = {name: f"what {name} carries" for name, _ in FIELDS}
    written["boundary"] = "compaction"
    del written[field]
    return "\n".join(f"{name}: {value}" for name, value in written.items()) + "\n"


class _AConfigurationStating:
    """A configuration this reader cannot produce, for the one state it has to read.

    ⛔ Built rather than loaded, and the reason is the rule under test: § 25
    refuses a project that runs the memory third and states no block, so a
    configuration in that state is one no file in this repository can reach. It
    is still a state `thirds` has to answer, because § 1 resolves a work tree
    against that tree's own surface -- so a tree cut before § 25 states no block
    and was ruled by a surface that marked none. ⚠️ The permissive reading of it
    runs a third with no store, which is what makes the arm worth an object.
    """

    def __init__(self, **values):
        self.values = values

    def get(self, path, default=None):
        return self.values.get(path, default)


def _an_entry(**overrides) -> str:
    """A complete memory entry, to break in a stated way."""
    written = {name: f"what {name} carries" for name, _ in ENTRY_FIELDS}
    written["provenance"] = "measured"
    written.update(overrides)
    return "\n".join(
        f"{name}: {value}" for name, value in written.items() if value is not None
    ) + "\n"


def _an_entry_without(field: str) -> str:
    written = {name: f"what {name} carries" for name, _ in ENTRY_FIELDS}
    written["provenance"] = "measured"
    del written[field]
    return "\n".join(f"{name}: {value}" for name, value in written.items()) + "\n"


# The prose the fixture below puts under its fence, named so the arm asserting
# the fact was recovered compares against one string rather than two literals.
A_STORED_FACT = "a fact somebody wrote down, in prose and in no form at all"


def _a_stored_entry(body: str = A_STORED_FACT) -> str:
    """One entry in the shape a store whose admission never ran actually holds.

    ⛔ **The measured shape and not an invented one**: a leading YAML document
    carrying a name, a one-line description and a subject label, then the fact as
    prose. ⚠️ The subject label is the whole reason § 25 forbids mining the
    leading document for the form's fields -- it is the key a reader would reach
    for, and `project` is a subject rather than an evidence class, so taking it
    as a provenance would make every fact in the store measured by construction.
    """
    return (
        f"{FENCE}\n"
        "name: a-fact\n"
        "description: one line about it, which the index carries\n"
        "metadata:\n"
        "  type: project\n"
        f"{FENCE}\n"
        "\n"
        f"{body}\n"
    )


# (label, how to write it, a fragment the refusal has to name). ⛔ One per arm of
# the admission, and the provenance arms are the ones § 25 spends the rule on: a
# fact admitted with no provenance is the one a later pass turns into a measured
# one by reading it twice.
ENTRY_PLANTED = [
    ("a fact with no provenance", lambda: _an_entry_without("provenance"),
     "`provenance` is missing"),
    ("a fact with nothing it was established from",
     lambda: _an_entry_without("source"), "`source` is missing"),
    ("a fact stating no premise", lambda: _an_entry_without("premise"),
     "`premise` is missing"),
    ("a provenance outside its set", lambda: _an_entry(provenance="obvious"),
     "`provenance` is 'obvious'"),
    ("a premise written empty", lambda: _an_entry(premise='""'),
     "`premise` is written and empty"),
    ("a field the entry form does not carry", lambda: _an_entry(asof="today"),
     "`asof` is not a field of the form"),
    ("a fact carrying a block rather than an answer",
     lambda: _an_entry(fact="\n  what: it claims"), "`fact` carries a block"),
    ("an empty entry", lambda: "", "the memory entry is empty"),
    ("an entry that does not parse", lambda: "fact: [unclosed\n",
     "the memory entry"),
]


# (label, how to write it, a fragment the refusal has to name)
PLANTED = [
    ("a field left out", lambda: _without("acceptance"), "`acceptance` is missing"),
    ("the boundary left out", lambda: _without("boundary"), "`boundary` is missing"),
    ("a field written empty", lambda: _an_artifact(committed='""'), "`committed` is written and empty"),
    ("a boundary outside its set", lambda: _an_artifact(boundary="whenever"), "`boundary` is 'whenever'"),
    ("a field the form does not carry", lambda: _an_artifact(mood="hopeful"),
     "`mood` is not a field of the form"),
    ("a field carrying a block rather than an answer",
     lambda: _an_artifact(acceptance="\n  what: it asks"), "`acceptance` carries a block"),
    ("a field carrying a list rather than an answer",
     lambda: _an_artifact(asked="[one, two]"), "`asked` carries a list"),
    ("a field carrying a boolean rather than an answer",
     lambda: _an_artifact(acceptance="false"), "`acceptance` carries false"),
    # ⛔ Both an extra key YAML reads as text and one it reads as a number, which
    # is the pair that made the report raise instead of reporting: one of each
    # cannot be sorted against the other.
    ("extra fields keyed by text and by a number together",
     lambda: _an_artifact(mood="hopeful", **{"1": "stray"}),
     "`1` is not a field of the form"),
    ("an artifact that is not a block of fields", lambda: "- just a list\n",
     "not a block of fields"),
    ("an empty artifact", lambda: "", "the save artifact is empty"),
    ("an artifact of nothing but a comment", lambda: "# a save that did not happen\n",
     "the save artifact is empty"),
    ("an artifact that does not parse", lambda: "boundary: [unclosed\n", "the save artifact"),
]


def _an_example_file_whose_carrier_is(carrier: str) -> str | None:
    """The path of the first example configuring § 25 that way.

    Found by the value rather than named, which is the rule the reader's own
    fixtures follow: a file this code pointed at would be the toolkit naming one
    project's tracker, and a carrier no example illustrates has to fail here
    rather than quietly borrow the other arm's file.
    """
    for name in sorted(os.listdir(config.EXAMPLES)):
        if not name.endswith((".yaml", ".yml")):
            continue
        path = os.path.join(config.EXAMPLES, name)
        with open(path, encoding="utf-8") as handle:
            data = config._load_yaml(handle.read(), config.CONFIG_PATH)
        if isinstance(data, dict) and (data.get(MEMORY_KEY) or {}).get(
            "carrier"
        ) == carrier:
            return path
    return None


def _an_example_whose_carrier_is(carrier: str) -> dict | None:
    """The same example, as a parsed block of keys."""
    path = _an_example_file_whose_carrier_is(carrier)
    if path is None:
        return None
    with open(path, encoding="utf-8") as handle:
        return config._load_yaml(handle.read(), config.CONFIG_PATH)


def _resolved(data: dict) -> config.Config:
    with open(config.SURFACE, encoding="utf-8") as handle:
        facts = config.surface_facts(handle.read())
    return config._resolve(data, config.EXAMPLES, facts, False)


def _a_checkout_and_a_tree(root: str) -> tuple[str, str]:
    """A real checkout with a real linked worktree beside it.

    ⛔ Built with git rather than faked, because what is under test is a reading
    git gives: a fixture of two directories would assert this module's own
    arithmetic over a shape the hazard never comes in. ⚠️ This is the measured
    case § 25 is written from -- a session standing in the second of these gets a
    different store derived for it, with nothing said.
    """
    import subprocess  # noqa: PLC0415 -- the arms that need a repository

    checkout = os.path.join(root, "checkout")
    os.makedirs(checkout)
    quiet = {"cwd": checkout, "check": True, "capture_output": True}
    subprocess.run(["git", "init", "-q", "-b", "main"], **quiet)
    # ⚠️ An identity with no address in it, which git accepts and the names sweep
    # requires: an address identifies a person or an account on a service, and
    # this repository carries none anywhere. Found by that gate on this change.
    subprocess.run(["git", "config", "user.email", "a-planted-identity"], **quiet)
    subprocess.run(["git", "config", "user.name", "A Planted Author"], **quiet)
    with open(os.path.join(checkout, "a-file"), "w", encoding="utf-8") as handle:
        handle.write("a tracked file, so there is a commit to branch from\n")
    subprocess.run(["git", "add", "a-file"], **quiet)
    subprocess.run(["git", "commit", "-q", "-m", "a planted commit"], **quiet)
    tree = os.path.join(root, "a-tree")
    subprocess.run(
        ["git", "worktree", "add", "-q", "-b", "a-planted-branch", tree], **quiet
    )
    return checkout, tree


def _memory_arms(check) -> None:
    """§ 25's half of this module, asserted over real directories and real files."""
    import subprocess  # noqa: PLC0415 -- the concurrency and the git arms
    import tempfile  # noqa: PLC0415

    # --- the entry form, and the admission it is the whole of ---------------
    complete = _an_entry()
    recovered, problems = read_entry(complete)
    check("a complete memory entry holds", not problems, f"reported {problems!r}")
    for name, _carries in ENTRY_FIELDS:
        check(
            f"`{name}` survives the round trip",
            (recovered or {}).get(name) is not None,
            f"recovered {recovered!r}",
        )
    for label, write, named in ENTRY_PLANTED:
        _recovered, found = read_entry(write())
        check(
            f"{label} is refused, naming it",
            any(named in problem for problem in found),
            f"reported {found!r}",
        )
    # ⛔ The two forms are held apart as well as each held: a field of one
    # accepted by the other would be a save writing a memory entry into the
    # artifact, or the reverse, with both forms reporting it held.
    check(
        "the artifact's own fields are not a memory entry",
        bool(read_entry(_an_artifact())[1]),
        "an artifact passed the entry form, so the two are one form wearing two "
        "names",
    )
    check(
        "and a memory entry is not a save artifact",
        bool(read(complete)[1]),
        "an entry passed the artifact form, which is the same collapse the other "
        "way round",
    )
    check(
        "no field is shared between the two forms",
        not ({name for name, _ in FIELDS} & {name for name, _ in ENTRY_FIELDS}),
        "a field in both forms is a field whose meaning depends on which file it "
        "is in, which no reader of either can tell",
    )

    # --- the read-time half, over the shape the measured store holds --------
    #
    # ⛔ The store a derived carrier hands over has been through no admission, so
    # every entry in it is in this shape and none of them carries the two fields
    # the rule requires. These arms are what makes that store readable rather
    # than refused whole, and each of them holds the direction that under-claims.
    check(
        "every standing a reader's answer produces is one this module names",
        set(PREMISE_ANSWERS.values()) == set(STANDINGS),
        f"answers produce {sorted(set(PREMISE_ANSWERS.values()))!r} and the "
        f"standings named are {STANDINGS!r} -- a standing nothing names is one a "
        "reader cannot place",
    )
    check(
        "the value an unstated provenance reads as is one of the two the form "
        "states, and not the measured one",
        UNSTATED_READS_AS in PROVENANCE and UNSTATED_READS_AS != "measured",
        f"reads as {UNSTATED_READS_AS!r}: a value outside the set is one no reader "
        "can place, and the measured one turns a passed-on fact into an observed "
        "one by leaving a field out",
    )

    stored = _a_stored_entry()
    status, got = recalled(stored)
    check(
        "an entry in the store's own shape is read rather than refused",
        status == 0 and got["holds"] is True and got["shape"] == "the store's own",
        f"exited {status} with {got!r} -- a reading that refuses the whole entry "
        "tells its reader nothing about what they are holding",
    )
    check(
        "and its fact is recovered from the prose under the fence",
        (got["read"] or {}).get("fact") == A_STORED_FACT,
        f"recovered {got['read']!r}",
    )
    check(
        "while the fields it does not carry come back named as unstated",
        got["unstated"] == ["premise", "provenance", "source"],
        f"named {got['unstated']!r}",
    )
    check(
        "and no key of its leading document is read as one of them",
        (got["read"] or {}).get("provenance") is None
        and (got["read"] or {}).get("source") is None,
        f"recovered {got['read']!r} -- the key on offer is a subject label, so a "
        "mapping invented here makes every fact in the store measured",
    )
    check(
        "a fact stating no provenance reads as the unstated reading",
        got["reads_as"] == UNSTATED_READS_AS,
        f"reads as {got['reads_as']!r}",
    )
    check(
        "and nothing checked leaves it unchecked rather than current",
        got["standing"] == UNCHECKED,
        f"stands as {got['standing']!r}",
    )
    # ⛔ The arm the whole standing exists for, and the one a permissive reading
    # would pass: there was no premise to check, so an answer that it holds is an
    # assertion about the fact rather than a reading of it.
    status, got = recalled(stored, "holds")
    check(
        "`holds` over an entry stating no premise is refused, and the fact is not "
        "reported current",
        status == 1
        and got["standing"] == UNCHECKED
        and any("nothing was checked" in problem for problem in got["problems"]),
        f"exited {status} with {got!r}",
    )
    status, got = recalled(stored, "broken")
    check(
        "a premise the reader found broken makes even an unprovenanced fact stale",
        status == 1 and got["standing"] == STALE,
        f"exited {status} with {got!r}",
    )
    # ⛔ And the admission keeps every bit of its reach: an entry *in the form*
    # with a field missing is refused, never read through the lenient arm. ⚠️ The
    # direction that matters -- a lenient reader that swallowed the form's own
    # refusals would have retired the admission by adding a second way in.
    status, got = recalled(_an_entry_without("provenance"))
    check(
        "an entry in the form with a field missing is still refused, not read "
        "leniently",
        status == 1
        and got["shape"] == "the entry form"
        and any("`provenance` is missing" in problem for problem in got["problems"]),
        f"exited {status} with {got!r}",
    )
    for answer, expected, expected_status in (
        ("holds", CURRENT, 0),
        ("broken", STALE, 1),
        ("unchecked", UNCHECKED, 0),
    ):
        status, got = recalled(complete, answer)
        check(
            f"a complete entry whose premise is answered {answer!r} stands as "
            f"{expected!r} and exits {expected_status}",
            status == expected_status and got["standing"] == expected,
            f"exited {status} with {got!r}",
        )
    # ⛔ A premise the form accepts and a truthiness test would not: `_held` lets
    # a number through, an identifier being one, so a falsy-but-present premise
    # has to read as *stated* here or the refusal's own message is false about
    # the entry. Found by review on this change -- the direction was safe and the
    # sentence was not.
    status, got = recalled(_an_entry(premise=0), "holds")
    check(
        "a premise the form accepts and that is falsy is still a premise stated",
        status == 0 and got["standing"] == CURRENT and not got["problems"],
        f"exited {status} with {got!r}",
    )
    status, got = recalled(complete)
    check(
        "and a stated provenance is read as the entry states it",
        got["reads_as"] == "measured" and got["unstated"] == [],
        f"reads as {got['reads_as']!r} with {got['unstated']!r} unstated",
    )
    status, got = recalled(complete, "obviously")
    check(
        "a premise answered outside the three is refused, not taken as one of them",
        status == 1 and got["standing"] == UNCHECKED,
        f"exited {status} with {got!r}",
    )
    status, got = recalled(_a_stored_entry(body="   "))
    check(
        "an entry with nothing under its fence is refused, naming the absent fact",
        status == 1
        and any("no fact to recall" in problem for problem in got["problems"]),
        f"exited {status} with {got!r}",
    )
    status, got = recalled(f"{FENCE}\nname: [unclosed\n{FENCE}\n\nthe fact itself\n")
    check(
        "a leading document that does not parse changes nothing about the fields",
        status == 0
        and (got["read"] or {}).get("fact") == "the fact itself"
        and got["unstated"] == ["premise", "provenance", "source"],
        f"exited {status} with {got!r} -- none of the three would have been taken "
        "out of that document either way",
    )
    status, got = recalled("just some prose, in neither shape\n")
    check(
        "a file in neither shape has no fact to read out of it, and says that",
        status == 1
        and got["read"] is None
        and got["standing"] == UNCHECKED
        and any("nothing to read a fact out of" in line for line in got["report"])
        and got["shape"] == "the entry form"
        # ⚠️ And its field list is sorted like the fenced arm's: one reader meets
        # both, so an order that depends on which arm answered is an order a
        # caller cannot compare. Asserted against the sort rather than against a
        # list written here, which would be this file's own spelling.
        and got["unstated"] == sorted(name for name, _ in ENTRY_FIELDS),
        f"exited {status} with {got!r}",
    )

    with tempfile.TemporaryDirectory() as root:
        checkout, tree = _a_checkout_and_a_tree(root)

        # --- which directory is a tree, read from git --------------------
        in_checkout, from_checkout = standing_in_a_tree(checkout)
        in_tree, from_tree = standing_in_a_tree(tree)
        check(
            "the checkout is read as the checkout",
            in_checkout is False,
            f"came back {in_checkout!r}",
        )
        check(
            "the linked tree is read as a tree",
            in_tree is True,
            f"came back {in_tree!r} -- this is the reading the whole refusal "
            "rests on",
        )
        check(
            "and both answers name the same checkout to run from",
            from_checkout is not None
            and os.path.realpath(from_checkout) == os.path.realpath(from_tree),
            f"came back {from_checkout!r} and {from_tree!r}",
        )
        outside = os.path.join(root, "no-repository")
        os.makedirs(outside)
        unplaced, _ = standing_in_a_tree(outside)
        check(
            "a directory git cannot place comes back unanswered, not as a checkout",
            unplaced is None,
            f"came back {unplaced!r} -- the permissive reading here is the one "
            "that writes a tree's own store",
        )

        # --- the write decision, both carriers and both policies ---------
        pinned_data = _an_example_whose_carrier_is("path")
        derived_data = _an_example_whose_carrier_is("derived")
        check(
            "an example pins its store, so the `path` arm is exercised",
            pinned_data is not None,
        )
        check(
            "an example leaves it to the harness, so the `derived` arm is too",
            derived_data is not None,
        )
        if pinned_data is None or derived_data is None:
            return

        store = os.path.join(root, "a-store")
        pinned_data[MEMORY_KEY]["store"] = store
        pinned_data[MEMORY_KEY]["index"] = "the-index.md"
        pinned_any = _resolved(pinned_data)
        placed = memory(pinned_any, tree)
        check(
            "a pinned store resolves to the stated path, whatever tree asked",
            placed["store"] == os.path.normpath(store),
            f"resolved {placed['store']!r}",
        )
        check(
            "and its index sits inside that store",
            placed["index"] == os.path.join(os.path.normpath(store), "the-index.md"),
            f"resolved {placed['index']!r}",
        )
        check(
            "a pinned store with `any_tree` is written from a tree",
            placed["may_write"] is True,
            f"decided {placed['may_write']!r}: {placed['report']!r}",
        )
        # ⛔ The two other spellings § 25's fence allows, asserted because each is
        # resolved here rather than by the reader -- which keeps a path as
        # written. A relative one resolved against the working directory instead
        # of the skills root would land in whichever tree asked, which is the
        # hazard this facet exists to close arriving through its own carrier.
        relative = {**pinned_data, MEMORY_KEY: {**pinned_data[MEMORY_KEY],
                                                "store": "a-relative-store"}}
        against_root = memory(_resolved(relative), tree)
        check(
            "a relative store resolves against the skills root, not the tree",
            against_root["store"]
            == os.path.join(os.path.abspath(config.EXAMPLES), "a-relative-store"),
            f"resolved {against_root['store']!r}",
        )
        tilde = {**pinned_data, MEMORY_KEY: {**pinned_data[MEMORY_KEY],
                                             "store": os.path.join("~", "a-store")}}
        check(
            "and a `~`-relative one is expanded rather than taken literally",
            memory(_resolved(tilde), tree)["store"]
            == os.path.join(os.path.expanduser("~"), "a-store"),
            f"resolved {memory(_resolved(tilde), tree)['store']!r}",
        )

        # ⛔ The same configuration with the one key changed, so the decision is
        # asserted against the key that makes it rather than against a second
        # fixture that differs in more than one way.
        strict = {**pinned_data, MEMORY_KEY: {**pinned_data[MEMORY_KEY],
                                              "write_from": "main_tree"}}
        strict_config = _resolved(strict)
        refused = memory(strict_config, tree)
        allowed = memory(strict_config, checkout)
        check(
            "the same store with `main_tree` refuses from a tree",
            refused["may_write"] is False,
            f"decided {refused['may_write']!r}: {refused['report']!r}",
        )
        check(
            "and the refusal names the checkout it would run from",
            any("checkout" in line for line in refused["report"]),
            f"reported {refused['report']!r}",
        )
        check(
            "the same store with `main_tree` is written from the checkout",
            allowed["may_write"] is True,
            f"decided {allowed['may_write']!r}: {allowed['report']!r}",
        )
        unplaced_decision = memory(strict_config, outside)
        check(
            "and from a directory git cannot place it is unanswered, not permitted",
            unplaced_decision["may_write"] is None,
            f"decided {unplaced_decision['may_write']!r}",
        )

        harness = memory(_resolved(derived_data), checkout)
        check(
            "a derived store resolves to no path at all",
            harness["store"] is None and harness["index"] is None,
            f"resolved {harness['store']!r} and {harness['index']!r}",
        )
        # ⛔ Three rather than two, and each named by the thing that makes it its
        # own half: a count alone would pass a report that stated one of them
        # twice. ⚠️ The admission arm is the one this project measured missing
        # from the report while the carrier was already leaving it open -- the
        # surface priced the derived arm at two costs when it has three.
        check(
            "and names the three halves it leaves open rather than two",
            len(harness["unclosed"]) == 3
            and any("lock" in line for line in harness["unclosed"])
            and any("renamed" in line for line in harness["unclosed"])
            and any("admission" in line for line in harness["unclosed"]),
            f"named {harness['unclosed']!r}",
        )
        absent = memory(
            _AConfigurationStating(**{"session.parts": list(ORDER)}), checkout
        )
        check(
            "a project carrying no block is told so rather than given a path",
            absent["carried"] is False and absent["may_write"] is None,
            f"came back {absent!r}",
        )
        # ⛔ The project that keeps no memory, which is a *shipped* configuration
        # and reaches this question through the restoring role whatever
        # `session.parts` says. ⚠️ Found by review on this change: without its own
        # arm it fell through to the `derived` branch and came back naming a
        # carrier the project does not state, two hazards it does not have, and a
        # write decision about a store that does not exist.
        keeps_none = _an_example_whose_carrier_is("none")
        check(
            "an example keeps no memory, so the arm below is asked",
            keeps_none is not None,
        )
        if keeps_none is not None:
            nothing = memory(_resolved(keeps_none), checkout)
            check(
                "a project that keeps no memory is told there is no store",
                nothing["carried"] is False
                and nothing["carrier"] == "none"
                and nothing["store"] is None
                and nothing["may_write"] is None
                and not nothing["unclosed"],
                f"came back {nothing!r}",
            )
            check(
                "and the answer names that carrier rather than another one",
                any("none" in line for line in nothing["report"])
                and not any("derived" in line for line in nothing["report"]),
                f"reported {nothing['report']!r}",
            )
        # ⛔ A pinned carrier whose keys the resolved surface did not require,
        # which is § 1's work-tree case: reported unanswered rather than composed
        # as a path named after a Python literal. Found by review.
        unkeyed = memory(
            _AConfigurationStating(**{f"{MEMORY_KEY}.carrier": "path"}), checkout
        )
        check(
            "a pinned carrier with no store to resolve is unanswered, not a path",
            unkeyed["store"] is None and unkeyed["may_write"] is None,
            f"came back {unkeyed!r}",
        )
        # ⛔ And the same for the key every branch of the decision quotes: an
        # absent one is unanswered rather than read as either word. Found by
        # review.
        unstated = memory(
            _AConfigurationStating(**{f"{MEMORY_KEY}.carrier": "derived"}), tree
        )
        check(
            "a carrier stating no tree a save may write from is unanswered",
            unstated["may_write"] is None
            and any("could not be established" in line
                    for line in unstated["report"]),
            f"came back {unstated!r}",
        )

        # --- the admission, at the point of writing ----------------------
        entry_path = os.path.join(root, "an-entry.yaml")
        with open(entry_path, "w", encoding="utf-8") as handle:
            handle.write(complete)
        bad_path = os.path.join(root, "a-bad-entry.yaml")
        with open(bad_path, "w", encoding="utf-8") as handle:
            handle.write(_an_entry_without("provenance"))

        status, answer = remember(pinned_any, tree, bad_path, "a-fact.md", "- a line")
        check(
            "an entry with no provenance is refused before anything is written",
            status == 1
            and answer["wrote"] is False
            and not os.path.exists(placed["index"]),
            f"exited {status} with {answer!r}, and the index "
            f"{'exists' if os.path.exists(placed['index']) else 'does not'}",
        )
        # ⛔ Read leniently, admitted strictly, and the two halves are held apart
        # here: the shape `recalled` above reads rather than refuses is still
        # refused at the point of writing, because a store that accepted it would
        # be a store carrying an unprovenanced fact by the one route the
        # admission exists to close.
        stored_path = os.path.join(root, "a-stored-entry.md")
        with open(stored_path, "w", encoding="utf-8") as handle:
            handle.write(_a_stored_entry())
        status, answer = remember(pinned_any, tree, stored_path, "a-fact.md", "- a line")
        check(
            "an entry in the store's own shape is refused at write time, read or not",
            status == 1 and answer["wrote"] is False,
            f"exited {status} with {answer!r} -- the lenient reading is for a store "
            "whose entries are already there, never a second way into one",
        )
        status, answer = remember(strict_config, tree, entry_path, "a-fact.md", "- a line")
        check(
            "a complete entry is still refused from a tree under `main_tree`",
            status == 1 and answer["wrote"] is False,
            f"exited {status} with {answer!r}",
        )
        status, answer = remember(pinned_any, tree, entry_path, "a-fact.md", "   ")
        check(
            "an entry with a blank index line is refused, being reachable by nothing",
            status == 1 and answer["wrote"] is False,
            f"exited {status} with {answer!r}",
        )
        status, answer = remember(
            _resolved(derived_data), checkout, entry_path, "a-fact.md", "- a line"
        )
        check(
            "a derived store has no index for this command to write, and says so",
            status == 1 and any("derived" in line for line in answer["problems"]),
            f"exited {status} with {answer!r}",
        )
        status, answer = remember(
            pinned_any, tree, os.path.join(root, "no-such-entry.yaml"), "a-fact.md",
            "- a line",
        )
        check(
            "an entry whose file cannot be read exits two, not one",
            status == 2,
            f"exited {status} with {answer!r}",
        )
        status, answer = remember(
            pinned_any, tree, entry_path, "a-fact.md", "- the first line"
        )
        check(
            "a complete entry under a pinned store is written, and the index with it",
            status == 0 and answer["wrote"] is True,
            f"exited {status} with {answer!r}",
        )
        with open(placed["index"], encoding="utf-8") as handle:
            check(
                "and the index carries the line it was handed",
                handle.read() == "- the first line\n",
                "the line the role handed over is not what the index holds",
            )
        check(
            "and the fact itself is placed in the store under the name handed over",
            answer.get("fact") == os.path.join(placed["store"], "a-fact.md")
            and os.path.isfile(answer["fact"]),
            f"placed {answer.get('fact')!r}",
        )
        with open(answer["fact"], encoding="utf-8") as handle:
            check(
                "with the entry's own text in it, unchanged",
                handle.read() == complete,
                "the file in the store is not what the role wrote",
            )
        # ⛔ Both ways a name reaches out of the store, and ⚠️ the index asserted
        # untouched after each: a refusal that had already appended the line
        # would leave an index pointing at a fact nobody wrote.
        before = open(placed["index"], encoding="utf-8").read()
        # ⛔ A store that will not take the fact, reported rather than raised out
        # of the one function whose contract is to name the problem. Planted by
        # making the name an existing directory, which is the cheapest real
        # instance of it. Found by review on this change.
        os.makedirs(os.path.join(placed["store"], "a-directory.md"), exist_ok=True)
        status, answer = remember(
            pinned_any, tree, entry_path, "a-directory.md", "- a line"
        )
        check(
            "a store that will not take the fact is reported, not raised",
            status == 1
            and answer["wrote"] is False
            and any("would not take" in line for line in answer["problems"]),
            f"exited {status} with {answer!r}",
        )
        for label, named in (
            ("a name that is a path", "elsewhere/a-fact.md"),
            ("a name that climbs out of the store", "../a-fact.md"),
            ("a name that is absolute", "/tmp/a-fact.md"),
            ("a name that is blank", "   "),
        ):
            status, answer = remember(
                pinned_any, tree, entry_path, named, "- a line"
            )
            check(
                f"{label} is refused, and the index is left alone",
                status == 1
                and answer["wrote"] is False
                and open(placed["index"], encoding="utf-8").read() == before,
                f"exited {status} with {answer!r}",
            )

        # --- the index, which is the one file two sessions contend on -----
        #
        # ⛔ Two arms, because only one of them reaches the lock, and that was
        # **measured rather than reasoned about**: with the `flock` call removed
        # from `_append_under_lock`, twelve writers appending one short line each
        # still kept all twelve lines and the count arm below stayed green, while
        # the exclusion arm under it was the single assertion that reddened. So
        # the count arm holds the outcome § 25 states and the exclusion arm holds
        # the mechanism it rests on, and neither stands in for the other.
        child = [
            sys.executable,
            "-c",
            "import sys; sys.path.insert(0, sys.argv[1]); import save; "
            "save._append_under_lock(sys.argv[2], sys.argv[3])",
            os.path.dirname(os.path.abspath(__file__)),
        ]
        index = placed["index"]
        writers = [
            subprocess.Popen([*child, index, f"- line {n}\n"]) for n in range(12)
        ]
        for writer in writers:
            writer.wait()
        with open(index, encoding="utf-8") as handle:
            written = handle.read().splitlines()
        check(
            "twelve sessions writing at once lose none of each other's entries",
            all(f"- line {n}" in written for n in range(12))
            and len(written) == 13,
            f"the index holds {len(written)} lines: {written!r}",
        )

        try:
            import fcntl  # noqa: PLC0415
        except ImportError:
            fcntl = None
        check(
            "this platform has the lock, so the exclusion below is asserted",
            fcntl is not None,
            "without `fcntl` the append happens and the lock does not, which is "
            "stated in `_append_under_lock` and is not what this runs on",
        )
        if fcntl is not None:
            holder = open(index, "a", encoding="utf-8")
            try:
                fcntl.flock(holder.fileno(), fcntl.LOCK_EX)
                blocked = True
                try:
                    subprocess.run(
                        [*child, index, "- a line nobody should see yet\n"],
                        timeout=2, capture_output=True, check=False,
                    )
                    blocked = False
                except subprocess.TimeoutExpired:
                    pass
                check(
                    "a second writer waits while the lock is held",
                    blocked,
                    "the append completed with another process holding the lock, "
                    "so the whole read-edit-write-back failure § 25 names is "
                    "open: this is the arm that reddens when the `flock` call "
                    "goes",
                )
            finally:
                fcntl.flock(holder.fileno(), fcntl.LOCK_UN)
                holder.close()


def self_test() -> int:
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

    print("the form, and the round trip that is what `resumable from the artifact` means")
    complete = _an_artifact()
    recovered, problems = read(complete)
    check("a complete artifact holds", not problems, f"reported {problems!r}")
    check(
        "and every field of the form is recovered from it",
        recovered is not None
        and all(recovered.get(name) for name, _ in FIELDS),
        f"recovered {recovered!r}",
    )
    # ⛔ The round trip asserted field by field rather than as a count: a form
    # that recovered the same number of fields under different names would pass a
    # count and fail a resume.
    for name, _carries in FIELDS:
        check(
            f"`{name}` survives the round trip",
            (recovered or {}).get(name) is not None,
            f"recovered {recovered!r}",
        )

    print()
    print("every way a written artifact fails the form")
    for label, write, named in PLANTED:
        _recovered, found = read(write())
        check(
            f"{label} is refused, naming it",
            any(named in problem for problem in found),
            f"reported {found!r}",
        )

    print()
    print("the thirds, in the procedure's order rather than a configuration's")
    # ⛔ Built from the surface's own vocabulary and stated in reverse, so an
    # implementation that passed a configuration's order through would be caught:
    # a fixture written in the right order asserts nothing about the ordering.
    live = config.load(config.REPO_ROOT)
    backwards = [entry["part"] for entry in _place(list(reversed(ORDER)))]
    check(
        "a configuration stating the thirds backwards gets the procedure's order",
        backwards == ORDER,
        f"came back {backwards!r}",
    )
    placed = [entry["part"] for entry in thirds(live)]
    check(
        "this project's own thirds come back in the procedure's order",
        placed == [name for name in ORDER if name in (live.get("session.parts") or [])],
        f"came back {placed!r}",
    )
    # ⛔ A third the surface states and this module places nowhere is reported as
    # unplaced rather than dropped, asserted on a stated third rather than on the
    # happy case.
    strange = _place(["commit", "telepathy"])
    check(
        "a third this module places nowhere comes back, reported as unplaced",
        [e["part"] for e in strange] == ["commit", "telepathy"]
        and [e["placed"] for e in strange] == [True, False],
        f"came back {strange!r}",
    )
    check(
        "and each one names what it reads",
        all(entry["reads"] for entry in thirds(live)),
        f"came back {thirds(live)!r}",
    )
    # ⛔ The availability arm, now that the one third whose mechanism was missing
    # has acquired one (§ 25). It is asserted in **both** directions over the two
    # configurations that produce them, rather than as an equivalence against a
    # set written here: a set would make this an assertion about this file's own
    # spelling, which is what the retired one was.
    live_memory = [e for e in thirds(live) if e["part"] == MEMORY_THIRD]
    check(
        "this project runs the memory third, so both arms below are asked",
        bool(live_memory) and live.get(f"{MEMORY_KEY}.carrier") is not None,
        f"came back {live_memory!r} -- with the third absent the arms assert "
        "nothing",
    )
    check(
        "a third whose block the project carries is reported available",
        all(entry["available"] for entry in live_memory),
        f"came back {live_memory!r}",
    )
    older = thirds(_AConfigurationStating(**{"session.parts": list(ORDER)}))
    check(
        "a third whose block is absent is reported unavailable rather than dropped",
        [entry["part"] for entry in older] == list(ORDER)
        and [entry["available"] for entry in older]
        == [name != MEMORY_THIRD for name in ORDER],
        f"came back {older!r}",
    )
    # ⛔ The one thing holding this module's reading to the surface's own
    # spelling. A block renamed on the surface would otherwise leave every
    # project's memory third reported unavailable, in silence and green -- which
    # is the exact shape the availability question replaced.
    with open(config.SURFACE, encoding="utf-8") as handle:
        surface_text = handle.read()
    check(
        "the block this module reads is one the surface declares",
        f"{MEMORY_KEY}.carrier" in config.surface_keys(surface_text),
        f"`{MEMORY_KEY}.carrier` is declared nowhere on the surface, so this "
        "module reads a key no project can write",
    )
    check(
        "and the third it reads that block for is one the surface states",
        MEMORY_THIRD in live.facts.get("lists", {}).get("session.parts", []),
        f"`{MEMORY_THIRD}` is not a third the surface states",
    )
    check(
        "the order this module places and the surface's vocabulary agree",
        set(ORDER) == set(live.facts.get("lists", {}).get("session.parts", [])),
        "a third the surface states is placed nowhere here, or the other way "
        "round -- either leaves a third running in an order nothing decided",
    )
    check(
        "every third this module places names what it reads",
        set(ORDER) <= set(READS),
        f"placed {ORDER!r} and names {sorted(READS)!r}",
    )
    # ⛔ The reader's own § 25 report, held against this module's: the two name
    # the same open halves, and nothing but this keeps them doing so. A reader
    # reporting a hazard this module does not, or the other way round, is a role
    # whose reply names one of the two and acts on the other.
    # ⚠️ Each arm is conditioned on the value that makes the reader report it, so
    # a project that pinned its store and lets any tree write it asserts neither
    # -- and the guard below is what keeps *this* project from silently becoming
    # that one while these two stay green over nothing.
    reported = live.unavailable()
    asked = 0
    if live.get(f"{MEMORY_KEY}.carrier") == "derived":
        asked += 1
        check(
            "the reader names the derived carrier among what it cannot close",
            any(f"{MEMORY_KEY}.carrier" in line for line in reported),
            f"reported {reported!r}",
        )
        # ⛔ And it names the same open halves this module does, **subject by
        # subject**. ⚠️ The arm above holds only that the key is mentioned, which
        # is exactly what let the two reports price this carrier at two costs
        # while the carrier already left three open: a list on one side and a
        # sentence on the other, compared by nothing. ⚠️ The three words are
        # written here, so what this reaches is that both reports name each
        # subject -- whether either states it correctly is the *quoting* kind of
        # judgement and is read.
        derived = memory(live, ".")
        for subject in ("lock", "renamed", "admission"):
            check(
                f"and `{subject}` is named by this module and by the reader alike",
                any(subject in line for line in derived["unclosed"])
                and any(subject in line for line in reported),
                f"this module named {derived['unclosed']!r} and the reader "
                f"{[line for line in reported if MEMORY_KEY in line]!r}",
            )
    if live.get(f"{MEMORY_KEY}.write_from") == "main_tree":
        asked += 1
        check(
            "and names the directories a save may not refresh memory from",
            any(f"{MEMORY_KEY}.write_from" in line for line in reported),
            f"reported {reported!r}",
        )
    check(
        "this project states at least one of the two, so the pair above was asked",
        asked > 0,
        "neither value this repository configures reaches the reader's § 25 "
        "report, so the two arms above are asserted over nothing",
    )

    print()
    print("§ 25's store, the write decision, and the entry a save may admit")
    _memory_arms(check)

    print()
    print("every documented exit status, on the path that produces it")
    import tempfile  # noqa: PLC0415 -- the arms that need a directory

    with tempfile.TemporaryDirectory() as root:
        check(
            "a project stating no configuration is told so rather than refused",
            main(["--skills-root", root]) == NOTHING_TO_ANSWER,
            "whoever invoked this by name is owed the answer that the project "
            "states nothing, which § 7 makes an invitation rather than silence",
        )
        # ⛔ The other three are asserted here because only the `3` path was,
        # which left the `0`/`1` split that is the whole point of `check` proved
        # by nothing. Found by review on this change.
        held = os.path.join(root, "holds.yaml")
        with open(held, "w", encoding="utf-8") as handle:
            handle.write(complete)
        check(
            "an artifact that holds exits zero",
            main(["check", "--file", held]) == 0,
        )
        broken = os.path.join(root, "broken.yaml")
        with open(broken, "w", encoding="utf-8") as handle:
            handle.write(_without("acceptance"))
        check(
            "an artifact that does not hold exits one",
            main(["check", "--file", broken]) == 1,
        )
        check(
            "an artifact whose file cannot be read exits two, not one",
            main(["check", "--file", os.path.join(root, "no-such-file.yaml")]) == 2,
            "a file that could not be opened has not failed the form, and a role "
            "told it failed would rewrite a file that is already right",
        )
        check("the form is answered with no configuration at all", main(["form"]) == 0)
        check(
            "and so is the entry form, which is procedure the same way",
            main(["entry"]) == 0,
        )
        entry = os.path.join(root, "an-entry.yaml")
        with open(entry, "w", encoding="utf-8") as handle:
            handle.write(_an_entry())
        check("an entry that holds exits zero", main(["recall", "--file", entry]) == 0)
        # ⛔ The two unlike things the `1` covers, each asserted on the path that
        # produces it: a form that failed, and a fact the reader reported stale.
        # ⚠️ A stale fact sharing the `0` of a current one is the restatement
        # § 25's standing rule exists against, read off the status alone.
        check(
            "and the same entry whose premise the reader found broken exits one",
            main(["recall", "--file", entry, "--premise", "broken"]) == 1,
        )
        check(
            "while one whose premise they found holding exits zero",
            main(["recall", "--file", entry, "--premise", "holds"]) == 0,
        )
        stored_file = os.path.join(root, "a-stored-entry.md")
        with open(stored_file, "w", encoding="utf-8") as handle:
            handle.write(_a_stored_entry())
        check(
            "an entry in the store's own shape exits zero rather than failing a "
            "form it is not in",
            main(["recall", "--file", stored_file]) == 0,
        )
        check(
            "and claiming its unstated premise holds exits one",
            main(["recall", "--file", stored_file, "--premise", "holds"]) == 1,
        )
        with open(entry, "w", encoding="utf-8") as handle:
            handle.write(_an_entry_without("premise"))
        check(
            "an entry that does not hold exits one",
            main(["recall", "--file", entry]) == 1,
        )
        check(
            "an entry whose file cannot be read exits two, not one",
            main(["recall", "--file", os.path.join(root, "no-entry.yaml")]) == 2,
        )
        # ⛔ The `memory` subcommand's own split, over a real skills root rather
        # than a fixture: a project that keeps no memory has nothing to answer
        # about, and reporting that as the status a failed question gets would
        # read a stated decision as a fault. Found by review on this change.
        source = _an_example_file_whose_carrier_is("none")
        keeps_none = _an_example_whose_carrier_is("none") or {}
        one_root = keeps_none.get("roots", {}).get("code") == "."
        check(
            "an example keeps no memory and states one code root, so the status "
            "below is asked",
            source is not None and one_root,
            "no example is in that shape, so this arm would be asserted over a "
            "configuration built here instead of one that ships",
        )
        if source is not None and one_root:
            adopter = os.path.join(root, "an-adopter")
            os.makedirs(os.path.join(adopter, ".claude"))
            with open(source, encoding="utf-8") as handle:
                written = handle.read()
            with open(os.path.join(adopter, config.CONFIG_PATH), "w",
                      encoding="utf-8") as handle:
                handle.write(written)
            check(
                "a project that keeps no memory exits with nothing to answer about",
                main(["memory", "--skills-root", adopter,
                      "--standing-in", adopter]) == NOTHING_TO_ANSWER,
                "a stated decision reported with the status a failed question "
                "gets reads as a fault",
            )

    print()
    check(
        "this run executed assertions rather than reporting a green nothing",
        ran > 1,
        "a suite that executes no case and exits zero is the degradation every "
        "check here is written against",
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

NOTHING_TO_ANSWER = 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="The bookkeeping role's thirds, and the form of its artifact.",
    )
    parser.add_argument("--skills-root", default=".")
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="what")

    # ⛔ Four subcommands take no `--skills-root`, and that is a removal rather
    # than an omission: a form is procedure and a reading holds a file it is
    # handed, so none of them reads a project's configuration at all. A flag
    # accepted and unread is a flag somebody passes and believes.
    sub.add_parser("form", help="the fields a save artifact carries")
    sub.add_parser("entry", help="the fields a memory entry carries (§ 25)")

    reading = sub.add_parser("check", help="hold a written artifact to the form")
    reading.add_argument("--file", required=True)

    recalling = sub.add_parser(
        "recall", help="read one written memory entry, and its standing (§ 25)"
    )
    recalling.add_argument("--file", required=True)
    # ⛔ The reader's own answer about the premise, defaulting to the one that
    # claims nothing: a default of `holds` would make *current* the value a
    # caller gets by not answering, which is the restatement § 24 refuses written
    # as a flag nobody passes.
    recalling.add_argument(
        "--premise", choices=sorted(PREMISE_ANSWERS), default="unchecked",
        help="what the reader found when they read the premise against the tree",
    )

    # ⛔ These two do read the configuration, and both take the working directory
    # explicitly rather than reading `os.getcwd()`: the decision they answer is
    # *about* a directory, so a caller asking about one it is not standing in --
    # the suite below, and a role reporting what a tree would get -- has to be
    # able to ask. ⚠️ The default is the current directory, which is the case a
    # role actually invokes.
    located = sub.add_parser("memory", help="§ 25's store, and the write decision")
    located.add_argument("--skills-root", default=".")
    located.add_argument("--standing-in", default=".")

    writing = sub.add_parser(
        "remember", help="admit one entry and append its index line under a lock"
    )
    writing.add_argument("--skills-root", default=".")
    writing.add_argument("--standing-in", default=".")
    writing.add_argument("--entry", required=True)
    writing.add_argument("--name", required=True)
    writing.add_argument("--line", required=True)

    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    # ⛔ Either form is this module's and is answered before any configuration is
    # read: both are procedure, so a project that configures nothing still has
    # them.
    if args.what == "form":
        print(json.dumps(form(), indent=2, ensure_ascii=False))
        return 0
    if args.what == "entry":
        print(json.dumps(entry_form(), indent=2, ensure_ascii=False))
        return 0

    if args.what in ("check", "recall"):
        try:
            with open(args.file, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            print(exc, file=sys.stderr)
            return 2
        # ⛔ A recalled entry is never handed back as a fact that is current:
        # § 24 obliges the reading role to check one, and a carrier that returned
        # the fact alone would have made the restatement the easier of the two
        # paths. What `recalled` adds over the form is where it says so -- the
        # standing, and what an entry stating no provenance reads as.
        if args.what == "recall":
            status, answer = recalled(text, args.premise)
            print(json.dumps(answer, indent=2, ensure_ascii=False))
            return status
        recovered, problems = read(text)
        answer = {"holds": not problems, "problems": problems, "read": recovered}
        print(json.dumps(answer, indent=2, ensure_ascii=False))
        return 0 if not problems else 1

    # ⛔ Asked before the configuration is loaded and answered rather than
    # refused, per § 7: whoever invoked this by name is owed the answer that the
    # project states nothing.
    if not config.configured(args.skills_root):
        print(json.dumps({
            "parts": [],
            "report": [
                "This project states no configuration, so nothing is known about "
                "its bookkeeping role. Write `.claude/mjolnir.yaml`; the keys are "
                "stated in the configuration surface shipped with the toolkit."
            ],
        }, indent=2, ensure_ascii=False))
        return NOTHING_TO_ANSWER

    try:
        configuration = config.load(args.skills_root)
    except (config.ConfigError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2

    if args.what == "memory":
        answer = memory(configuration, args.standing_in)
        answer["form"] = entry_form()
        print(json.dumps(answer, indent=2, ensure_ascii=False))
        # ⛔ Zero wherever the question was answered, whichever way it was
        # answered: a refusal to write from this directory is this command
        # working, and a caller reading a non-zero status as a broken run would
        # go looking for a fault instead of moving to the checkout.
        if answer["may_write"] is not None:
            return 0
        # ⛔ And the two remaining cases are apart, for the reason this module's
        # own exit statuses are apart at all: a project that states it keeps no
        # memory has *nothing to answer about*, while a decision nobody could
        # establish is a question that was asked and failed. Collapsing the first
        # into the second reports a stated decision as a fault. Found by review.
        if answer.get("carrier") == "none":
            return NOTHING_TO_ANSWER
        return 1

    if args.what == "remember":
        status, answer = remember(
            configuration, args.standing_in, args.entry, args.name, args.line
        )
        print(json.dumps(answer, indent=2, ensure_ascii=False))
        return status

    running = thirds(configuration)
    report = [
        f"`{entry['part']}` is mapped and its mechanism is absent, so the role "
        f"reports what it could not do: it reads {entry['reads']}."
        for entry in running
        if not entry["available"]
    ]
    report += [
        f"`{entry['part']}` is a third this module places nowhere, so the order "
        "it runs in is undecided (§ 23)."
        for entry in running
        if not entry["placed"]
    ]
    # ⛔ A third that runs and has nowhere to put its output reads exactly like
    # one that works, which is the direction the whole report exists against.
    # § 23 says the role reports the absent store rather than inventing a path,
    # and this is where it is handed that answer.
    if running and configuration.get("context.artifacts.carrier") == "none":
        report.append(
            "No artifact store is carried (`context.artifacts.carrier: none`), "
            "so there is nowhere for a save to write the artifact a later pass "
            "reads: the role reports that rather than inventing a path (§ 23)."
        )
    if not running:
        report.append(
            "No bookkeeping role runs here (`session.parts: []`), so there is no "
            "third to run and nothing to save (§ 23)."
        )
    # § 25's answer, carried in this report rather than left for the role to ask
    # about separately: the write decision is about the directory the role is
    # standing in, so a role that read it later -- after the tracker third, say,
    # or at the point of writing -- would have run two thirds before learning the
    # middle one refuses here.
    located = None
    if any(entry["part"] == MEMORY_THIRD for entry in running):
        located = memory(configuration, ".")
        report += located["report"]
        report += located["unclosed"]
    print(json.dumps(
        {"parts": running, "store": configuration.get("context.artifacts.carrier"),
         "memory": located, "report": report},
        indent=2, ensure_ascii=False,
    ))
    return 0 if running else NOTHING_TO_ANSWER


if __name__ == "__main__":
    sys.exit(main())
