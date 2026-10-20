#!/usr/bin/env python3
"""Hold a role's reply to the register the surface fixes for it.

The surface makes language, register and audience configurable per artifact and
fixes one of them: the reply a role writes in the session, whose audience the
project does not choose. That rule is procedure -- see the surface's § 8, *The
reply to the person running a role* -- and this is what holds a reply to it
instead of the writer's judgement at the time of writing.

It runs as a `Stop` hook, which is the only place the finished reply exists: the
harness hands the hook `last_assistant_message`, so nothing here parses a
transcript or guesses at what was sent.

⚠️ **Which properties are held, which are only reported, and every limit this
has are recorded once, in `docs/single-source-of-truth.md` § The reply's
register.** This docstring deliberately does not restate them: two prose copies
of a limit are the defect this repository exists to delete, and nothing holds a
docstring to a document.

The property list is read out of the surface at run time. A row added to that
table therefore reddens `--self-test` until somebody either holds it or states
why it is not held -- the same direction as the gate's orphan-section check, one
surface over. The patterns and the densities are grammar and live here.

Usage:
    check_reply_register.py              read a hook payload on stdin, answer on stdout
    check_reply_register.py --self-test  assert every check reddens on each of its
                                         planted violations, then hold the surface's
                                         property list to being wholly accounted for
"""

from __future__ import annotations

import io
import json
import os
import re
import sys
import tempfile
from pathlib import Path

# --- where the rule lives --------------------------------------------------

SURFACE = Path(__file__).resolve().parent.parent / "config" / "schema.md"

# The subsection whose table this script reads, by the anchor the code host
# would give its heading. Grammar: the heading text may be reworded without
# touching this script only if its anchor survives, which is the same bargain
# every citation of the surface already makes.
PROPERTY_TABLE_ANCHOR = "the-reply-to-the-person-running-a-role"

CITATION = "schema § 8 → The reply to the person running a role"

# The rule the Completeness property carries, cited rather than restated: it is
# the surface's first rule and this file holds one artifact of it.
DEFERRAL_CITATION = "schema § Nothing is deferred"

# What an answer that asks for a fix asks for, in one string because both of the
# answers that ask for one ask for the same thing: the reply just sent is the one
# carrying the findings, so a branch that told the writer the *next* reply would
# be better would be licensing a deferral — measured, and obeyed, when the arm
# that fires on a density closed on one. `--self-test` holds both asking answers
# to carrying this sentence and to promising nothing about a later reply.
#
# ⛔ **Asking is what costs the reader the reply a second time, and `decision` is
# not what decides it.** Context handed back on a `Stop` is read by the writer
# whether or not the answer also blocks, so an arm that reported a finding *and*
# asked for a restatement spent a whole re-read on a density — measured, and the
# price is recorded in the document rather than restated here. So an arm that
# does not block asks the writer for nothing and reports to the person instead,
# and `context` has a branch only where something is asked.
#
# ⚠️ `DEFERRALS` is a closed list, and it is the *quoting* weakness this
# repository rules out elsewhere -- safe only because what it sweeps is the
# strings authored below rather than arbitrary text. A reworded licence passes
# it; what catches that is the absent `RESTATE`, which is the arm that matters.
RESTATE = ("Re-send this reply corrected, in this turn — a finding against the reply just sent "
           "is not carried forward to a later one.")
DEFERRALS = ("the next reply", "a later reply", "written knowing", "next time")

# ⛔ What the two kinds now mean, which is narrower than it reads: `BLOCKS` hands
# the turn back and asks for the reply again, `REPORTS` reaches the person who
# ran the role and asks the writer for nothing at all. The second used to ask
# too, which made the distinction cost the same as the first.
BLOCKS, REPORTS = "blocks", "reports"

# The carrier that calls this script, and the event it registers for. Grammar:
# the path and the event name. ⛔ Held rather than assumed -- the carrier naming
# a script that is not this one, or an event that is not the one carrying a
# finished reply, leaves the gate green and the hook silently dead, which is the
# failure the workflow exists to catch.
CARRIER = Path(__file__).resolve().parent.parent / "hooks" / "hooks.json"
CARRIER_EVENT = "Stop"

# --- the grammars ----------------------------------------------------------
#
# Each is a form rather than a judgement, which is what makes a forbidding check
# sound. The thresholds below are deliberately not written into any document: a
# number in prose is a copy that has to be kept in sync, and a run prints its
# own.

# An opening that announces the reply instead of being it. Bare interjections
# need punctuation after them, because `Great care is needed` is not a preamble
# and `Great!` is.
PREAMBLE = re.compile(
    r"^\s*(?:"
    r"I'?ll\b|I will\b|I'?m going to\b|I am going to\b|I'?d be happy to\b|I'?ve been asked\b"
    r"|Let me\b|Let'?s\b|Let us\b|Now I'?ll\b|First,? I'?ll\b|Here'?s what I'?ll\b"
    r"|You asked\b|You'?re asking\b|As requested\b|As you requested\b|Based on your\b"
    r"|Happy to\b|Good question\b"
    r"|(?:Sure|Of course|Certainly|Absolutely|Great|Perfect|Excellent)\s*[,.!:;]"
    r")",
    re.I,
)

# Shortening by compression: text that has stopped being sentences. One arrow is
# a mapping and is legitimate -- `open → closed` says something a sentence would
# say worse -- so what is forbidden is the *chain*, and a chain is two arrows
# sharing an operand.
#
# ⚠️ The unit is the chain and not the line. A per-line budget was the first
# shape this check had and it was wrong in the direction that blocks: a reply's
# paragraph is one unwrapped line, so `#6 → #77 and separately #80 → #82` -- two
# unrelated legitimate mappings in one sentence -- read as a chain.
ARROW = re.compile(r"→|⇒|->|=>")

# What may sit between two arrows and leave them still sharing an operand. The
# length arm came first: a chain's operand is a word or two, and two mappings in
# a sentence have a clause between them.
OPERAND = re.compile(r"^\s*\S+(?:\s+\S+)?\s*$")

# ⛔ The length arm alone is not enough, because a clause can be one token.
# Measured on a reply this check handed back in a session of a project that has
# the plugin enabled: `FRESH` or `OURS` → write; `CHANGED` → report puts `write;`
# between its arrows, which share no operand at all, and the finding's own quoted
# span -- `'→ write;   →'` -- carried the semicolon that says so. The turn was
# handed back and the whole reply came back, eight of its thirteen lines byte for
# byte, for a compression that was not there.
#
# ⚠️ Clause-ending punctuation counts only where a clause ends: followed by
# whitespace, or ending the span between the arrows. A dot inside a token is not
# a boundary, so a chain of file paths stays a chain.
#
# ⚠️ The coordinators are a closed list, which is the *quoting* weakness this
# repository rules out elsewhere -- and it is safe here in the one direction that
# matters: a conjunction the list does not carry leaves a chain red. A finding
# kept rather than a finding invented.
CLAUSE_BOUNDARY = re.compile(
    r"[.;:,!?](?=\s|$)|[—–]|\b(?:and|or|but|then|while|whereas|plus|versus|vs)\b",
    re.I,
)

# Where compression stops being one line to restate and becomes the reply's
# texture. The floor is one, because a single chain is a finding and no reply is
# textured by one line; the other arm scales with the reply, so a long reply is
# not handed back at a density a short one is only told about.
CHAIN_FLOOR = 1
CHAIN_LINES = 6

# Emphasis as a default texture rather than as a mark on a load-bearing fact.
EMPHASIS = re.compile(r"\*\*[^*\n]+\*\*|__[^_\n]+__")
EMPHASIS_FLOOR = 4

# Narrative and dramatic texture. A closed list, because the alternative is
# sweeping prose for sentiment, which reddens on a reword.
DRAMATIC = re.compile(
    r"\b(?:dramatic(?:ally)?|massively|incredibl[ey]|enormously|wildly|shockingly|"
    r"brutal(?:ly)?|stunning(?:ly)?|astonishing(?:ly)?|catastrophic(?:ally)?|"
    r"devastating(?:ly)?|terrifying|horrif(?:ic|ying)|nightmare|disaster)\b",
    re.I,
)
# ⚠️ Not a bare `!`. `a != b` and an image's `![alt](…)` are punctuation and
# syntax rather than exclamation, and counting them raised the register finding
# on ordinary technical prose.
EXCLAMATION = re.compile(r"!(?![=\[])")
DRAMATIC_ALLOWED = 2

# Hedging throughout, as against uncertainty stated plainly and once. `rather
# than` is excluded: it is this repository's commonest construction and carries
# no hedge at all.
HEDGE = re.compile(
    r"\b(?:perhaps|possibly|arguably|probably|presumably|somewhat|"
    r"i think|i believe|i suspect|it seems|it appears|"
    r"might be|may be|kind of|sort of|more or less)\b",
    re.I,
)
HEDGES_ALLOWED = 3

# Work the reply names and the turn does not do. The rule is § Nothing is
# deferred's and is not restated here; what is written here is the grammar of the
# forms it was measured escaping through, which are all first person or addressed
# to the reader -- a reply parks work by promising it, offering it, or excusing
# its absence, never by describing somebody else's.
#
# ⛔ **The floor is one and it blocks.** Every other density arm in this file
# scales with the reply because a texture is the finding; here a single parked
# sentence is the whole violation, and the reply is the cheapest place in the
# loop to commit one -- no commit, no body, no thread, so no gate after it sees
# what was named.
#
# ⚠️ A closed list, which is the *quoting* weakness this repository rules out
# elsewhere, and safe in the one direction that matters: a reworded parking
# passes and leaves a finding missed, never a finding invented. What covers the
# rewordings is the person reading the reply, which is the mechanism this arm
# narrows rather than replaces.
#
# ⛔ **Four of these are named rather than derived**, by a ruling of 2026-10-20:
# `open items`, `deliberately`, `stated plainly`, and `left` -- and all four are
# matched only in their **parking senses**, by a ruling of the same date reading
# the measurement below. ⚠️ That is a narrowing rather than a softening, and it
# is the carve-out `left` already had, applied to the three forms that did not:
# matching one bare hands a turn back over text that parks nothing, which costs
# the reader the whole reply for a finding that is not there.
#
# `left` was held to have had it from the start, the bare word being this
# repository's ordinary English for what a process or a merge did -- *three
# trees left behind*. ⛔ **It had it in the third person only.** One alternative
# matched `I left` as a bare token, so the carve-out held for what a sibling
# session did and not for what the writer did, and the loop's own reply about
# work it had done reddened: *I left the tree and released the claim*, *I left a
# review comment on the thread*. Measured on the fourth hand-back, the day the
# other three were narrowed, and the green plant that was supposed to hold this
# carve-out asserted a sibling's tree rather than the writer's own sentence --
# so it could not reach the alternative that was bare.
#
# The other three were held to be distinctive enough that a reply has no other
# use for them, and ⚠️ **that premise failed the next day**, on a reply that paid
# the re-read for it. Each of the three is this repository's own vocabulary for a
# mechanism, and the bare form reddened on every sentence below:
#
#   - `deliberately` is how a design intent is recorded here, in nine of one
#     document's own section headings and in § 4's word for a facet nobody
#     configured. ⛔ **Measured on a reply**, which described when a mechanism
#     was built and how it behaves and owned no work at all;
#   - `open items` is the mechanism § Nothing is deferred *states* -- a gate
#     counts them on the change and refuses the merge while one stands -- so a
#     reply describing that gate reddened;
#   - `stated plainly` is § 8's own Uncertainty row, and the text of this
#     script's own finding for it, so a reply relaying this check reddened on it.
#
# ⚠️ The second and third were **demonstrated against the shipped check** rather
# than waited for, which is the direction a false red has to be established in:
# a sentence this repository writes by the dozen, run through the arm.
#
# ⚠️ **What parks in each is the writer's own absence**, which is the grammar the
# whole arm already states: an omission excused rather than filled, a section of
# work the reply carries rather than does, a gap stated in place of being closed.
# ⛔ The ruling is kept where it was measured -- the shape each form was named for
# stays red -- and `--self-test` holds every form in both directions.
PARKED = re.compile(
    # `open items`: one asserted to stand. ⚠️ Not the count a gate reads, which
    # is the rule's own mechanism, and not a *section* of them — that form is
    # read with its answer, below, since the answer can be that there are none.
    r"\bopen items? (?:remains?|stands?|(?:is|are) (?:listed|below|outstanding))\b"
    r"|\b(?:remains?|stands?) (?:as )?(?:an |one )?open item\b"
    r"|\b(?:leaves?|leaving|left) (?:behind )?(?:an |one |two |three |four |\d+ )?open items?\b"
    # `deliberately`: an absence of work excused rather than filled. ⚠️ Not
    # `deliberately does not`, which is how every surface here states a limit,
    # and not `deliberately not written`, which is how two of them state one.
    r"|\bdeliberately (?:absent|omitted|skipped|unfixed|undone|untouched|unfinished|incomplete)\b"
    r"|\bdeliberately (?:not|never) "
    r"(?:done|fixed|built|run|implemented|wired|added|filled|tested|touched|handled|covered)\b"
    # `stated plainly`: a gap stated in place of being closed. ⚠️ Not the plain
    # statement § 8 asks for, and not what is stated plainly *about* a gap.
    r"|\bstated plainly (?:rather than|instead of)\b"
    r"|\b(?:gaps?|limits?|costs?|residues?|absences?|omissions?|shortfalls?|holes?)\b"
    r"[^.\n]{0,40}?\bstated plainly\b"
    # `left`: the writer's own omission, excused rather than filled. ⚠️ Not the
    # bare word, and ⛔ **not the bare word in the first person either**, which
    # is what the loop's own reply says about work it did do -- *I left a review
    # comment*, *I left the tree and released the claim*. So it is read with the
    # parked state it leaves behind, over the bounded gap `stated plainly` above
    # is already read across. ⚠️ The person is not matched at all: the writer's
    # own omission and a sibling's read the same here, and the first person was
    # what shipped bare.
    r"|\b(?:left|leaving|leave) (?:it |them |that |this |these |those )?"
    r"(?:to|for|as) (?:a |the )?"
    r"(?:later|future|follow-?up|next|another|somebody|someone|whoever|you)\b"
    r"|\bleft (?:to do|undone|out|open|for later|for now)\b"
    r"|\bwhat(?:'?s| is) left\b"
    r"|\b(?:left|leaving|leave)\b[^.\n]{0,40}?"
    r"\b(?:undone|unfixed|unaddressed|unresolved|unfinished|untouched)\b"
    r"|\bnext steps?\b"
    r"|\bfollow-?ups?\b"
    r"|\b(?:still|yet) to (?:be )?(?:done|built|written|fixed|run)\b"
    r"|\bremain(?:s|ing) (?:to be )?(?:done|built|written|fixed)\b"
    r"|\bout of scope\b"
    r"|\b(?:for|in) (?:a |the )?later (?:pass|turn|reply|item|session|change)\b"
    r"|\bsay the word\b"
    r"|\btell me (?:to|if|which)\b[^.\n]{0,60}?\band I(?:'?ll| will)\b"
    r"|\bif you(?:'?d like|'?d prefer| want)(?:,)? I can\b"
    r"|\bI have(?:n'?t| not) (?:touched|done|built|run|fixed|started|implemented)\b"
    r"|\bwhich I have(?:n'?t| not)\b"
    r"|\bTODO\b",
    re.I,
)
PARKED_FLOOR = 1

# ⛔ The one ruled form that is read with its answer rather than as a span. A
# section of open items is a finding where it lists any, and the gate on the
# change's body already holds the same section to being answered with one
# string and nothing else -- so a reply carrying that answer states that it
# parked nothing, and handing it back is the false red this arm is being
# narrowed to stop. ⚠️ The spellings are that gate's, deliberately alike: a
# reply and a body answering the same question differently would be two
# conventions for one rule. The heading is matched on its text at any level,
# and the label form carries its answer on the same line.
OPEN_ITEMS_SECTION = re.compile(
    r"^\s{0,3}(?:#{1,6}\s*|(?:\*\*|__)\s*)?open items?\s*(?:\*\*|__)?"
    r"\s*(?::\s*(?P<answer>\S.*?))?\s*$",
    re.I,
)
NO_OPEN_ITEMS = re.compile(r"^\s*(?:[-*+]\s+)?none\.?\s*$", re.I)

# ⚠️ A fence is matched with its marker captured, not as a bare ```` ``` ````.
# A toggle on any fence line inverts on the *nested* fence that showing a
# markdown fence requires, and everything after it then reads as code — the
# whole rest of a reply silently unchecked, which is the one failure a checker
# must not have. So an open block records its marker and only a fence of the
# same character and at least that length closes it, which is the host's own
# rule.
FENCE = re.compile(r"^\s{0,3}(?P<marker>`{3,}|~{3,})")
# Markdown's other code block, which carries no marker at all.
INDENTED_CODE = re.compile(r"^(?: {4,}|\t)")
CODE_SPAN = re.compile(r"`[^`\n]*`")
TABLE_ROW = re.compile(r"^\s*\|")
HEADING = re.compile(r"^\s*#{1,6}\s+")
QUOTE = re.compile(r"^\s*>")
# A line that is a break or a bolded stand-in for a heading. Neither is the
# reply's opening sentence, and both let a preamble on the next line through.
NOT_AN_OPENING = re.compile(r"^\s*(?:(?:[-*_]\s*){3,}|(?:\*\*|__)[^*_\n]+(?:\*\*|__)\s*:?)\s*$")


# --- reading the reply -----------------------------------------------------


def prose(reply: str, *, tables: bool = False) -> list[str]:
    """The lines of a reply that are prose, in order.

    Code goes whole — fenced blocks by their marker, indented blocks by their
    indent — and inline code spans are removed from the lines that survive. A
    quoted line is not the writer's own text, so it is not held against them. A
    table row is prose only where a check asks for it: a cell is where this
    repository's own documents put a mapping arrow and a bolded term, so
    sweeping rows would redden on the shape the register asks for.

    ⚠️ The indent rule over-reaches in the safe direction: a list item's
    four-space continuation line is read as code and checked by nothing. That
    is a finding missed rather than a finding invented, which is the right way
    round for the two checks that block.
    """
    out, marker = [], None
    for line in reply.splitlines():
        fence = FENCE.match(line)
        if fence:
            found = fence.group("marker")
            if marker is None:
                marker = found
            elif found[0] == marker[0] and len(found) >= len(marker):
                marker = None
            continue
        if marker is not None or not line.strip():
            continue
        if INDENTED_CODE.match(line) or QUOTE.match(line):
            continue
        if TABLE_ROW.match(line) and not tables:
            continue
        out.append(CODE_SPAN.sub(" ", line))
    return out


def opening(reply: str) -> str:
    """The first line that carries the reply's own words."""
    for line in prose(reply, tables=True):
        if HEADING.match(line) or NOT_AN_OPENING.match(line):
            continue
        return re.sub(r"^\s*(?:[-*+]|\d+\.)\s+", "", line)
    return ""


def chains(line: str) -> list[str]:
    """Each pair of arrows in one line that shares an operand, from the one to the other.

    Read pair by pair rather than by one pattern over the line, because *sharing*
    is a property of the text between two particular arrows: four arrows in a
    sentence can be one chain, two chains, or a mapping and a chain, and a match
    against the whole line cannot say which of those it found.
    """
    found, arrows = [], list(ARROW.finditer(line))
    for left, right in zip(arrows, arrows[1:]):
        between = line[left.end():right.start()]
        if OPERAND.match(between) and not CLAUSE_BOUNDARY.search(between):
            found.append(line[left.start():right.end()])
    return found


# --- the checks ------------------------------------------------------------
#
# Each returns a list of findings. A finding is one sentence naming the property
# and what in the reply failed it, because the reply is what gets restated and a
# finding that does not say where is a finding nobody can act on.


def check_opening_is_the_finding(reply: str) -> list[str]:
    first = opening(reply)
    if PREAMBLE.match(first):
        return [
            f"Opening: the reply opens with a preamble — {first[:60].strip()!r} — rather than "
            "with the finding or the outcome."
        ]
    return []


def check_no_compression(reply: str) -> list[str]:
    findings = []
    for line in prose(reply):
        for chain in chains(line):
            findings.append(
                f"Length: text is compressed into an arrow chain — {chain.strip()[:60]!r}. "
                "Shortening is by selection, never by compression."
            )
    # ⚠️ Three is enough to act on and a wall of them is not, but the cap is
    # reported rather than silent: a bounded finding list that reads as the
    # whole truth is the same defect as a check that holds nothing.
    if len(findings) > 3:
        dropped = len(findings) - 3
        findings = findings[:3] + [
            f"Length: {dropped} further compressed line(s) are not listed; compression is "
            "spread through the reply rather than sitting in one line."
        ]
    return findings


def check_compression_is_not_the_texture(reply: str) -> list[str]:
    lines = prose(reply)
    count = sum(len(chains(line)) for line in lines)
    allowed = max(CHAIN_FLOOR, len(lines) // CHAIN_LINES)
    if count > allowed:
        return [
            f"Length: {count} arrow chains across {len(lines)} prose lines is compression as the "
            f"reply's texture rather than one line to restate (over {allowed}), which is what "
            "hands the turn back."
        ]
    return []


def check_emphasis_is_not_the_texture(reply: str) -> list[str]:
    lines = prose(reply)
    spans = sum(len(EMPHASIS.findall(line)) for line in lines)
    allowed = max(EMPHASIS_FLOOR, len(lines) // 3)
    if spans > allowed:
        return [
            f"Emphasis: {spans} emphasised spans across {len(lines)} prose lines reads as a "
            f"default texture rather than as a mark on a load-bearing fact (over {allowed})."
        ]
    return []


def check_register_is_reference(reply: str) -> list[str]:
    # A word list has no reason to exempt a table: a dramatic word in a cell is
    # the same word. Only the chain check excludes rows, because a cell is where
    # a mapping legitimately lives.
    body = "\n".join(prose(reply, tables=True))
    hits = len(DRAMATIC.findall(body)) + len(EXCLAMATION.findall(body))
    if hits > DRAMATIC_ALLOWED:
        return [
            f"Register: {hits} dramatic words or exclamations read as narrative rather than as "
            f"a textbook stating a result (over {DRAMATIC_ALLOWED})."
        ]
    return []


def check_uncertainty_is_stated_once(reply: str) -> list[str]:
    body = "\n".join(prose(reply, tables=True))
    hits = len(HEDGE.findall(body))
    if hits > HEDGES_ALLOWED:
        return [
            f"Uncertainty: {hits} hedges read as hedging throughout rather than as uncertainty "
            f"stated plainly and once (over {HEDGES_ALLOWED})."
        ]
    return []


def check_nothing_is_parked(reply: str) -> list[str]:
    """Work the reply names and the turn does not do.

    ⛔ The one check here whose rule is not § 8's. It holds this artifact to the
    surface's first rule, which already says it reaches a role's own reply; what
    the property adds is that the same hook holds it, rather than the writer
    noticing at the time of writing -- which is the mechanism § 8 says is being
    replaced for every other row of its table.

    ⚠️ A table cell is swept like prose. The forms this arm reads are sentences a
    writer puts in a cell as readily as in a paragraph -- a `verdict` column
    saying *next steps* parks exactly what a sentence would.
    """
    lines = prose(reply, tables=True)
    found = []
    for index, line in enumerate(lines):
        for match in PARKED.finditer(line):
            start = max(0, match.start() - 24)
            found.append(line[start:match.end() + 24].strip())
        section = OPEN_ITEMS_SECTION.match(line)
        if not section:
            continue
        # ⚠️ The answer is on the label's own line or on the next line of prose,
        # blanks having been dropped already. A section with nothing after it at
        # all has answered nothing, which is the heading's own finding.
        answer = section.group("answer")
        if answer is None:
            answer = lines[index + 1] if index + 1 < len(lines) else ""
        if not NO_OPEN_ITEMS.match(answer):
            found.append(line.strip())
    if len(found) < PARKED_FLOOR:
        return []
    # ⚠️ Bounded like the compression arm, and for the same reason: three spans
    # are enough to act on, and a bounded list that reads as the whole truth is
    # the defect a check is for.
    shown = found[:3]
    more = (f" {len(found) - 3} further span(s) are not listed." if len(found) > 3 else "")
    return [
        f"Completeness: the reply names work this turn does not do ({DEFERRAL_CITATION}) — "
        + "; ".join(repr(s) for s in shown)
        + f".{more} The work goes under the current branch, pull request and item, or the one "
        "question that blocks it is asked instead."
    ]


# Which property of the surface's table each check holds, and what a finding on
# it does. ⛔ `BLOCKS` is for a finding that is a fact about the text *and* worth
# what handing a turn back costs, which is the whole reply a second time -- the
# writer restates it entire and the person reads a reply they have already read.
# So the opening blocks on one instance, being the first thing read and the frame
# for everything under it; compression blocks where it is the reply's texture
# rather than one line, which is a density; and a check whose rule is reached
# only through a word list or a density reports. The keys are asserted against
# the surface below, in both directions.
HELD = {
    "Opening": [("the opening is the finding", BLOCKS, check_opening_is_the_finding)],
    "Length": [
        ("shortening is by selection", REPORTS, check_no_compression),
        ("compression is not the texture", BLOCKS, check_compression_is_not_the_texture),
    ],
    "Emphasis": [("emphasis is not the texture", REPORTS, check_emphasis_is_not_the_texture)],
    "Register": [("the register is reference", REPORTS, check_register_is_reference)],
    "Uncertainty": [("uncertainty is stated once", REPORTS, check_uncertainty_is_stated_once)],
    # ⛔ `BLOCKS` on one span, which no other arm here does. The cost of a
    # hand-back is the whole reply a second time, and it is the right price for
    # this one: the alternative is the person reading parked work and saying so,
    # which is what the rule exists to stop them having to do.
    "Completeness": [("nothing is parked", BLOCKS, check_nothing_is_parked)],
}

# What no check here holds, and whether that is the whole property or half of it.
# ⚠️ `PARTIAL` is load-bearing rather than descriptive: a property that is half
# held must also appear in HELD, and a wholly unheld one must not. Without the
# distinction, `Length` being excused here would keep the accounting green after
# its check was deleted.
#
# ⚠️ The reasons are deliberately absent. They are stated once, in
# `docs/single-source-of-truth.md`, and a copy of them here is a copy nothing
# holds -- which is what the two already had, having drifted in wording before
# either was a week old.
WHOLE, PARTIAL = "whole", "partial"
RESIDUE = {
    "Structure": WHOLE,
    "Length": PARTIAL,
}


def read_properties(text: str) -> list[str]:
    """The first column of the register table, read out of the surface.

    The table is found by the anchor of the subsection it sits in rather than by
    its heading text or its position, for the reason the gate's own rulings
    table is found by a column header: a renumbering must not be a change this
    script has to be edited for. Reading stops at the next heading of any level,
    so a table added below the subsection is not parsed as a continuation of
    this one.
    """
    found, fenced, properties = False, False, []
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        heading = HEADING.match(line)
        if heading:
            if found:
                break
            title = re.sub(r"^\s*#{1,6}\s+", "", line).strip().lower().replace("`", "")
            found = re.sub(r"[^\w\s-]", "", title).replace(" ", "-") == PROPERTY_TABLE_ANCHOR
            continue
        if not found or not TABLE_ROW.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        head = re.sub(r"[*`]", "", cells[0]) if cells else ""
        if not head or set(head) <= set("-: ") or head == "Property":
            continue
        if head not in properties:
            properties.append(head)
    return properties


def check_every_property_is_accounted_for(text: str) -> list[str]:
    """The direction nobody remembers to check by hand.

    A property added to the surface's table with no check and no stated reason
    for having none is the register growing a clause this script silently does
    not hold. It fails here, at the moment the row is added.
    """
    declared = read_properties(text)
    problems = []
    if not declared:
        problems.append(
            f"{SURFACE.name}: no register table was found under `{PROPERTY_TABLE_ANCHOR}`, so "
            "this script holds nothing. Either the subsection moved or its heading no longer "
            "slugs to that anchor."
        )
        return problems
    accounted = set(HELD) | set(RESIDUE)
    for name in declared:
        if name not in accounted:
            problems.append(
                f"{SURFACE.name}: the register's `{name}` property is held by no check and no "
                "reason is stated for leaving it unheld."
            )
    for name in sorted(accounted - set(declared)):
        problems.append(
            f"{name}: this script holds or excuses a property the surface's register table does "
            "not carry. A check with nothing behind it is a copy of a rule that has moved."
        )
    # ⛔ Held or excused is not the same answer, and conflating them is how a
    # deleted check reads as a stated limit. A property excused in part must
    # still be held in part, and one excused whole must be held by nothing.
    for name, extent in RESIDUE.items():
        if extent == PARTIAL and name not in HELD:
            problems.append(
                f"{name}: excused in part, which says the rest of it is held — and no check "
                "holds it. A half-excused property with no check is a limit stated over nothing."
            )
        if extent == WHOLE and name in HELD:
            problems.append(
                f"{name}: excused whole and also held by a check. One of the two is wrong, and "
                "the document states whichever this file does not."
            )
    return problems


def check_the_carrier_still_calls_this(text: str) -> list[str]:
    """Is the hook still wired to this script, on the event that carries a reply?

    ⛔ The checker holding itself proves nothing about the carrier. A renamed
    script, a mistyped expansion of the plugin's own root, a wrong event name or
    a carrier that stopped being valid JSON all leave every check here green and
    the hook dead — the one failure mode that reports success. So the carrier is
    read and what it names is resolved.
    """
    try:
        carrier = json.loads(text)
    except ValueError as error:
        return [f"{CARRIER.name}: is not valid JSON ({error}), so the harness registers no hook."]
    handlers = (carrier.get("hooks") or {}).get(CARRIER_EVENT) or []
    commands = [
        " ".join([entry.get("command", "")] + list(entry.get("args") or []))
        for matcher in handlers
        for entry in (matcher.get("hooks") or [])
    ]
    if not commands:
        return [
            f"{CARRIER.name}: registers no `{CARRIER_EVENT}` command. {CARRIER_EVENT} is the "
            "event that carries a finished reply, so nothing else can hold one."
        ]
    mine = Path(__file__).resolve()
    for command in commands:
        for token in command.split():
            # The harness expands its own root into the carrier; resolving it
            # from this file is the same path by construction.
            candidate = token.replace("${CLAUDE_PLUGIN_ROOT}", str(mine.parent.parent))
            if candidate.endswith(mine.name) and Path(candidate).resolve() == mine:
                return []
    return [
        f"{CARRIER.name}: its `{CARRIER_EVENT}` command does not resolve to {mine.name} "
        f"({'; '.join(commands)}). The checks here hold nothing the harness runs."
    ]


# --- the answer the harness reads ------------------------------------------


def findings(reply: str) -> tuple[list[str], list[str]]:
    """(blocking, reported) findings against one reply."""
    blocking, reported = [], []
    for tests in HELD.values():
        for _, kind, test in tests:
            (blocking if kind == BLOCKS else reported).extend(test(reply))
    return blocking, reported


def already_blocked(turn: str, *, record: bool) -> tuple[bool, str]:
    """Has this turn been handed back once already? And if unknown, why.

    The guard is per turn and not per session: a reply restated once has had its
    chance, and a hook that blocks the restatement too would hold the session
    open on a judgement the forbidding checks cannot make. ⚠️ The identifier is
    the harness's own turn id, and a payload without one falls back to the
    session, which blocks once per session rather than once per turn — the
    conservative direction.

    ⛔ **The marker records a hand-back and not a fire**, which is what `record`
    is for: the caller passes it only where this answer would hand the turn back,
    so an answer that reports spends nothing. While every answer asked for a
    restatement the two were the same event; once one of them stopped asking, a
    density would have spent the turn's one hand-back and the blocking finding
    after it would have been told, falsely, that it had already had one.

    ⛔ Where the state cannot be kept, this reports rather than blocks, because
    a guard that cannot read itself cannot promise to stop — but it **says
    which** rather than returning the same answer as a turn that has genuinely
    had its hand-back. Silence there would make a hook that never blocks
    indistinguishable from one doing its job.
    """
    root = os.environ.get("CLAUDE_PLUGIN_DATA")
    if not root:
        # ⚠️ Per user, not per host: a shared temporary directory is created by
        # whoever runs first, and every later user's marker write is refused.
        root = os.path.join(tempfile.gettempdir(), f"reply-register-{os.getuid()}")
    seen = Path(root) / "reply-register-turns"
    try:
        seen.mkdir(parents=True, exist_ok=True)
        marker = seen / re.sub(r"[^A-Za-z0-9_-]", "-", turn)[:120]
        if marker.exists():
            return True, ""
        if record:
            marker.touch()
    except OSError as error:
        return True, f"the turn guard could not keep state ({type(error).__name__}: {seen})"
    # ⚠️ Pruning is best-effort and separate: a marker another process unlinked
    # between the listing and the stat raises, and that must not be read as this
    # turn having been handed back already.
    try:
        files = sorted(seen.iterdir(), key=lambda p: p.stat().st_mtime)
        for stale in files[:-500]:
            stale.unlink(missing_ok=True)
    except OSError:
        pass
    return False, ""


def answer(payload: dict) -> dict:
    reply = payload.get("last_assistant_message") or ""
    if not reply.strip():
        return {}
    blocking, reported = findings(reply)
    if not blocking and not reported:
        return {}

    # ⚠️ `prompt_id` is the turn; `session_id` is the fallback, and blocking once
    # per session is the conservative answer where the turn is not named. A
    # payload naming neither cannot be guarded at all, and that is reported
    # rather than treated as a turn that has had its hand-back.
    turn = str(payload.get("prompt_id") or payload.get("session_id") or "")
    if not turn:
        unguarded = "no turn or session is named in the payload, so the one-hand-back guard "\
                    "cannot be kept"
        # ⚠️ Not handed back rather than unknown: a payload naming no turn has
        # had no hand-back, and the message to the person must not say it has.
        handed_back, block = False, False
    else:
        # ⚠️ `record` is the blocking findings and not `block`, which is derived
        # from the answer this call returns: a hand-back is recorded exactly
        # where there is something to hand back for and the turn has not had
        # one, which is the same condition as `block` without the circle.
        handed_back, unguarded = already_blocked(turn, record=bool(blocking))
        block = bool(blocking) and not handed_back

    # ⛔ Asked of the writer only where a hand-back is warranted *and* a
    # restatement is still owed: either the turn is handed back, or a finding
    # that would have been could not be guarded. A spent hand-back has had its
    # restatement and a density was never worth one, and both of those reach the
    # person instead -- which is the whole of what `REPORTS` costs now.
    if not (block or (blocking and unguarded)):
        return {"systemMessage": told(blocking, reported, handed_back)}

    out: dict = {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": context(blocking, reported, block, unguarded),
        }
    }
    if block:
        out["decision"] = "block"
        out["reason"] = (
            f"The reply's register is procedure ({CITATION}). "
            + "; ".join(f.split(":", 1)[0] for f in blocking)
            + " — handed back once for restating."
        )
    else:
        out["systemMessage"] = (
            f"Reply register: {len(blocking) + len(reported)} finding(s) against {CITATION}. "
            f"Nothing was handed back: {unguarded}."
        )
    return out


def told(blocking: list[str], reported: list[str], handed_back: bool) -> str:
    """What the person who ran the role reads when the writer is asked for nothing.

    The findings themselves and not a count of them: this is the only place they
    are said now, so a message carrying the number alone would report that the
    register held something without saying what. ⚠️ A blocking finding reaching
    this message says so, because a spent hand-back and a density are the same
    answer to the writer and are not the same fact about the reply.
    """
    lines = [f"Reply register: {len(blocking) + len(reported)} finding(s) against {CITATION}."]
    lines += [f"  - {f}" for f in blocking + reported]
    if blocking and handed_back:
        lines.append("  Nothing more is asked: this turn has had its one hand-back.")
    return "\n".join(lines)


def context(blocking: list[str], reported: list[str], block: bool, unguarded: str = "") -> str:
    """What the writer is asked for, on the two answers that ask for anything.

    ⛔ There is no third branch. One closed on *the next reply is written knowing
    them*, which is a deferral stated by the guard that holds the rule against
    deferring, and the shape that replaced it asked for a whole restatement on a
    density. What those two arms do now is report to the person, above.
    """
    lines = [f"The reply's register is procedure: {CITATION}. Findings against the reply just sent:"]
    lines += [f"- {f}" for f in blocking + reported]
    if block:
        lines.append(
            f"This turn is handed back once only; a second reply is not blocked. {RESTATE}"
        )
    else:
        lines.append(
            f"Nothing is blocked, and not because these findings are weak: {unguarded}. {RESTATE}"
        )
    return "\n".join(lines)


def hook(stream, out=None) -> int:
    """Answer one payload. ⛔ Fails open, and says so.

    A hook that crashes on every turn is worse than one that holds nothing, and
    a hook that holds nothing while reporting green is worse than both. So an
    internal failure answers with a message naming itself rather than with
    silence or with a non-zero exit.

    ⚠️ **It can only say so once it is running.** A failure before that — the
    harness's timeout, no interpreter on the path, a syntax error in this file —
    produces no output and nothing in the session says the reply was held to
    nothing. That residue is irreducible from inside the hook, and what covers
    it is the gate: this script's own run asserts the checks still fire and that
    the carrier still calls it.
    """
    out = out if out is not None else sys.stdout
    try:
        payload = json.load(stream)
        answered = answer(payload if isinstance(payload, dict) else {})
    except Exception as error:  # noqa: BLE001 — any failure here must stay non-fatal
        print(json.dumps({
            "systemMessage": (
                f"Reply register: the check did not run ({type(error).__name__}), so this "
                "reply was held to nothing."
            )
        }), file=out)
        return 0
    if answered:
        print(json.dumps(answered), file=out)
    return 0


# --- the planted violations ------------------------------------------------
#
# One per branch that does real work, including the branches that must stay
# green: a check that reddens on an arrow inside a fenced block is not the check
# this file claims to carry.

CLEAN = (
    "Three relations were added and one was refused.\n\n"
    "| edge | why |\n|---|---|\n| #6 ← #77 | setup cannot generate a key it does not know |\n\n"
    "The refusal is in `tools/check_single_source.py`, which reads the anchor set at run time.\n"
)

REDDENS = [
    ("the opening is the finding", "an announcing opening",
     "I'll read the configuration and report what it carries.\n"),
    ("the opening is the finding", "a bare interjection with punctuation",
     "Sure! The configuration carries six facets.\n"),
    ("the opening is the finding", "an opening that restates the request",
     "You asked which issues are unblocked. Twenty-nine are.\n"),
    ("the opening is the finding", "an announcing opening under a heading",
     "## Findings\n\nLet me walk through what the sweep found.\n"),
    ("shortening is by selection", "a line crushed into an arrow chain",
     "The sweep reads: file → region → span → value.\n"),
    ("shortening is by selection", "an ascii arrow chain",
     "Order is row 0 -> row 1 -> row 8.\n"),
    ("shortening is by selection", "a chain of file paths, whose dots sit inside tokens",
     "The sweep walks tools/a.py -> tools/b.py -> tools/c.py in that order.\n"),
    ("compression is not the texture", "compression as the reply's texture",
     "Reading is a → b → c.\nWriting is d → e → f.\nRefusing is g → h → i.\n"),
    ("emphasis is not the texture", "emphasis as a default texture",
     "The **sweep** holds **nine** checks over **two** scopes, and **seven** of them are "
     "**forbidding**, which is **most** of the script.\n"),
    ("the register is reference", "dramatic texture",
     "The result is catastrophic! The sweep is brutally wrong, and the fallout is devastating.\n"),
    ("uncertainty is stated once", "hedging throughout",
     "It seems the sweep possibly misses a case, and I think it might be arguably unsound, "
     "though presumably somewhat narrow.\n"),
    ("the opening is the finding", "an announcing opening under a thematic break",
     "---\n\nLet me walk through what the sweep found.\n"),
    ("the opening is the finding", "an announcing opening under a bolded pseudo-heading",
     "**Summary**\n\nLet me walk through what the sweep found.\n"),
    ("shortening is by selection", "a chain of more arrows than the cap reports",
     "a → b → c.\nd → e → f.\ng → h → i.\nj → k → l.\n"),
    ("the register is reference", "exclamations alone, with no dramatic word",
     "The sweep is green! The gate is green! The hook is green!\n"),
    ("the register is reference", "a dramatic word in a table cell",
     "| finding | verdict |\n|---|---|\n| the sweep | catastrophic, devastating, a disaster |\n"),
    ("emphasis is not the texture", "emphasis over the line-count arm rather than the floor",
     "".join(f"Line {i} carries **one** emphasised **span** pair.\n" for i in range(12))),
    ("nothing is parked", "work named under a heading the writer does not act on",
     "The three trees are gone.\n\n## Next steps\n\nDelete the five branches.\n"),
    ("nothing is parked", "the measured shape: work named and the turn ended",
     "Two things that follow, which I haven't touched: the skill's own wording, and the ignore "
     "entry.\n"),
    ("nothing is parked", "an offer in place of the work",
     "The guard is written and its plants are green. Say the word and I will wire the carrier.\n"),
    ("nothing is parked", "a conditional offer, which is the same parking",
     "The arm reddens on one span. If you want, I can add the density arm as well.\n"),
    ("nothing is parked", "an omission excused rather than filled",
     "The second reading is deliberately absent, and the first covers the measured case.\n"),
    ("nothing is parked", "a ruled phrase carrying a section of work rather than doing it",
     "The guard is wired and its plants are green.\n\n## Open items\n\n- the skill's own wording\n"),
    ("nothing is parked", "a ruled phrase asserting that one of them stands",
     "The arm is narrowed. One open item remains against this change.\n"),
    ("nothing is parked", "the same section as a label, answered with work",
     "The guard is wired.\n\nOpen items: the skill's own wording\n"),
    ("nothing is parked", "the same section answered with nothing at all",
     "The guard is wired and its plants are green.\n\n## Open items\n"),
    ("nothing is parked", "the writer's own omission, excused with the state it leaves behind",
     "The carrier is wired and its plants are green. I have left the second arm unfixed.\n"),
    ("nothing is parked", "the same, with the object between the word and the state",
     "The narrowing is in. I left the density arm the sweep asks for undone.\n"),
    ("nothing is parked", "a ruled phrase stating a gap in place of closing it",
     "The second arm's cost is stated plainly rather than fixed, and the first covers the "
     "measured case.\n"),
    ("nothing is parked", "parking in a table cell, where a sentence would be read",
     "| part | verdict |\n|---|---|\n| the sweep arm | out of scope |\n"),
    ("nothing is parked", "work handed to the reader",
     "The branches are deleted. Tell me which of the two to narrow and I will.\n"),
]

STAY_GREEN = [
    ("the opening is the finding", "a reply that opens with its finding", CLEAN),
    ("shortening is by selection", "arrows inside a fenced block",
     "The mapping is stated once.\n\n```\nfile -> region -> span -> value\n```\n"),
    ("shortening is by selection", "arrows inside a code span",
     "The trigger is `pull_request -> * -> push -> main` and nothing else.\n"),
    ("shortening is by selection", "a mapping arrow in a table row",
     "| from | to |\n|---|---|\n| #6 → #77 → #80 | the installer half |\n"),
    ("shortening is by selection", "one mapping arrow in a sentence",
     "The status moves open → closed and nothing else writes it.\n"),
    ("the register is reference", "a dramatic word inside a code span",
     "The planted value is `disaster` and the check reddens on it.\n"),
    ("uncertainty is stated once", "uncertainty stated plainly once",
     "The threshold is a proxy: it may be wrong on a long reply. Nothing else here is "
     "uncertain.\n"),
    ("shortening is by selection", "arrows inside an indented code block",
     "The traceback:\n\n    a -> b -> c\n    d -> e -> f\n"),
    ("shortening is by selection", "arrows inside a tilde fence",
     "Shown below.\n\n~~~\na -> b -> c\n~~~\n"),
    ("shortening is by selection", "a chain inside a nested fence, with prose after it",
     "The register is held once.\n\n````markdown\n```\na -> b -> c\n```\n````\n\n"
     "The gate holds the checker, not the reply.\n"),
    ("shortening is by selection", "a quoted chain, which is not the writer's text",
     "> you said a -> b -> c\n\nThat mapping is now stated on the surface.\n"),
    ("shortening is by selection", "two unrelated mappings in one sentence",
     "Dependencies: #6 → #77 and separately #80 → #82.\n"),
    # ⚠️ The measured false red, kept as the plant that holds the carve-out it
    # cost. One token between the arrows, and that token ends a clause.
    ("shortening is by selection", "two mappings a clause apart, sharing no operand",
     "Writing is decided per key: `FRESH` or `OURS` → write; `CHANGED` → report the key and "
     "leave the value alone.\n"),
    ("compression is not the texture", "one chain, which is a line to restate and not a texture",
     "The sweep reads: file → region → span and nothing else does.\n"),
    ("compression is not the texture", "arrows inside a fenced block",
     "The mapping is stated once.\n\n```\nfile -> region -> span -> value\n```\n"),
    ("the register is reference", "an inequality and an image, which are not exclamations",
     "The guard compares a != b and c != d.\n\n![one](a.png) ![two](b.png) ![three](c.png)\n"),
    # ⚠️ The narrowing each ruled form cost, kept as the plants that hold it.
    # Every sentence below is this repository's ordinary prose about a mechanism,
    # a design intent or a rule, and a bare match hands the turn back over each.
    ("nothing is parked", "the past tense of leaving a tree, which parks nothing",
     "The sibling session left its tree and the release then succeeded.\n"),
    # ⚠️ The same carve-out in the first person, which is where it was in fact
    # bare: each sentence below is the loop's own reply about work it did do, and
    # the fourth hand-back was paid on the third of them.
    ("nothing is parked", "the writer leaving a tree, which is the loop's own cleanup",
     "I left the tree and released the claim, and the branch is deleted on both sides.\n"),
    ("nothing is parked", "the writer leaving a review comment, which is work done",
     "I left a review comment on each of the two threads the diff opened.\n"),
    ("nothing is parked", "a file correctly unchanged, which is a judgement and not a parking",
     "Every dangling pointer is repointed. I left the narrative prose in one session summary "
     "alone, since that sentence records which file a past session edited.\n"),
    ("nothing is parked", "a residue count, which is a fact and not a promise",
     "Three worktrees remain registered and six branches survive the merge.\n"),
    # ⚠️ The measured false red, in the shape it was handed back in: a reply that
    # reports when a mechanism was built and how it behaves, owning no work at all.
    ("nothing is parked", "somebody else's design intent, reported",
     "The step is deliberately not a plain entry in the list: it is skipped with a warning "
     "unless the setting it reads is already there.\n"),
    ("nothing is parked", "a citation of one of the nine section headings here that carry the word",
     "The limit is recorded under § What this check deliberately does not hold.\n"),
    ("nothing is parked", "a limit this repository states about its own documents",
     "The densities are deliberately not written down in any document, and a run prints its "
     "own.\n"),
    ("nothing is parked", "the mechanism the no-deferral rule states, described",
     "The gate counts the open items raised against the change and refuses the merge while one "
     "stands.\n"),
    ("nothing is parked", "the section carrying the answer the sibling gate asks for",
     "The guard is wired and its plants are green.\n\n## Open items\n\nNone.\n"),
    ("nothing is parked", "the same answer under a label rather than a heading",
     "The guard is wired and its plants are green.\n\nOpen items: none\n"),
    ("nothing is parked", "the register's own Uncertainty row, cited",
     "That row asks for uncertainty stated plainly, once, and this reply carries one hedge.\n"),
    ("nothing is parked", "this check's own finding for that row, relayed",
     "The hook answered: four hedges read as hedging throughout rather than as uncertainty "
     "stated plainly and once.\n"),
    ("nothing is parked", "a ruled phrase inside a code span, which is a citation",
     "The gate reads the body's `## Open items` section and the threads on the change.\n"),
    ("nothing is parked", "a quoted parking, which is not the writer's text",
     "> next steps: wire the guard\n\nThat work is in this change, under this item.\n"),
    ("nothing is parked", "a reply that does the work and asks nothing",
     CLEAN),
]


# --- the plants against the surface ----------------------------------------
#
# ⛔ A plant may not name the content it plants into. The first draft spelled out
# a whole row of the register's table and the subsection's heading text, so
# rewording either made `str.replace` a no-op: the plant planted nothing, the
# self-test printed STAYED GREEN, and the workflow — whose only step this is —
# failed on an edit that was not a defect. Each plant below is written against
# what the parser just found, which is the same bargain the gate's rulings table
# struck when it stopped keying on a literal heading.


def _row_of(text: str, name: str) -> str:
    """The table row whose first cell is `name`, as it stands in the surface."""
    for line in text.splitlines():
        if TABLE_ROW.match(line):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and re.sub(r"[*`]", "", cells[0]) == name:
                return line
    raise AssertionError(f"no row for {name!r} to plant against")


def _heading_of(text: str) -> str:
    """The heading line whose anchor the parser keys on, as it stands."""
    for line in text.splitlines():
        if HEADING.match(line):
            title = re.sub(r"^\s*#{1,6}\s+", "", line).strip().lower().replace("`", "")
            if re.sub(r"[^\w\s-]", "", title).replace(" ", "-") == PROPERTY_TABLE_ANCHOR:
                return line
    raise AssertionError("no heading carrying the register table's anchor")


def _plant_unaccounted_property(text: str) -> str:
    first = read_properties(text)[0]
    row = _row_of(text, first)
    return text.replace(row, row + "\n| Cadence | Sentences that vary in length | A rhythm |")


def _plant_renamed_property(text: str) -> str:
    """Renaming reddens the unaccounted direction, so the name must stay held."""
    held = next(name for name in read_properties(text) if name in HELD)
    row = _row_of(text, held)
    return text.replace(row, row.replace(held, f"{held}Renamed", 1))


def _plant_removed_property(text: str) -> str:
    """The other direction, alone: a held property the table no longer carries.

    Removing the row leaves nothing unaccounted, so only the check-with-nothing-
    behind-it direction can redden on this — which is what makes it the plant
    that direction needed. Renaming reddens both at once and proved neither.
    """
    held = next(name for name in read_properties(text) if name in HELD)
    return text.replace(_row_of(text, held) + "\n", "")


def _plant_renamed_heading(text: str) -> str:
    heading = _heading_of(text)
    return text.replace(heading, re.sub(r"\brole\b", "roles", heading))


SURFACE_PLANTS = [
    ("a property with no check and no stated reason", _plant_unaccounted_property),
    ("a renamed property, leaving a check with nothing behind it", _plant_renamed_property),
    ("a held property the table stopped carrying", _plant_removed_property),
    ("a subsection whose heading no longer slugs to the anchor", _plant_renamed_heading),
]

CARRIER_PLANTS = [
    ("a carrier that is not valid JSON", lambda text: text.rstrip()[:-1]),
    ("a carrier registering no handler for the event",
     lambda text: text.replace(f'"{CARRIER_EVENT}"', '"PreToolUse"')),
    ("a carrier calling a script that is not this one",
     lambda text: text.replace("check_reply_register.py", "check_something_else.py")),
    ("a carrier whose expansion of the plugin root is mistyped",
     lambda text: text.replace("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOTS")),
]


def _plant_for(kind: str) -> str:
    """A planted reply whose answer carries the given kind — and, for a reported
    finding, carries nothing that blocks, since that is what the assertion is about.

    ⚠️ Chosen by what `findings()` answers rather than by position in `REDDENS`.
    The first draft indexed the list, so inserting a plant silently repointed the
    assertions about what blocks and what reports to whichever plants had moved
    into those slots. ⛔ And keying on the plant's own label is not enough
    either, now that one property is held by two checks: a line crushed into
    chains is reported per line *and* blocks as a texture, so a plant labelled
    for the reporting check can carry a blocking finding too — which would make
    `a reported finding blocks nothing` assert the opposite of what it says.
    """
    for _, _, reply in REDDENS:
        blocking, reported = findings(reply)
        if kind == BLOCKS and blocking:
            return reply
        if kind == REPORTS and reported and not blocking:
            return reply
    raise AssertionError(f"no planted reply produces a {kind} finding alone")


def self_test() -> int:
    by_name = {name: test for tests in HELD.values() for name, _, test in tests}
    failures = 0

    # ⚠️ Both directions, and neither raises. A plant naming a check that no
    # longer exists used to die on a KeyError, which is the gate's only step
    # returning a traceback instead of a verdict — the shape this repository
    # already recorded once for its sweep.
    for name, label, _ in REDDENS + STAY_GREEN:
        if name not in by_name:
            print(f"  PLANT WITHOUT A CHECK  {name}: {label}")
            failures += 1
    for name in by_name:
        if not any(n == name for n, _, _ in REDDENS):
            print(f"  NO PLANTED VIOLATION   {name}")
            failures += 1

    print(f"Asserting each check reddens on its planted violations ({len(REDDENS)}):")
    for name, label, reply in REDDENS:
        if name not in by_name:
            continue
        if by_name[name](reply):
            print(f"  red on                 {name}: {label}")
        else:
            print(f"  STAYED GREEN           {name}: {label}")
            failures += 1

    print(f"\nAsserting each stays green where it must ({len(STAY_GREEN)}):")
    for name, label, reply in STAY_GREEN:
        if name not in by_name:
            continue
        found = by_name[name](reply)
        if found:
            print(f"  FALSE RED              {name}: {label} — {found[0][:70]}")
            failures += 1
        else:
            print(f"  green on               {name}: {label}")

    text = SURFACE.read_text(encoding="utf-8")
    print(f"\nAsserting the property list is held to the surface ({len(SURFACE_PLANTS)}):")
    for label, plant in SURFACE_PLANTS:
        if check_every_property_is_accounted_for(plant(text)):
            print(f"  red on                 {label}")
        else:
            print(f"  STAYED GREEN           {label}")
            failures += 1

    carrier = CARRIER.read_text(encoding="utf-8")
    print(f"\nAsserting the carrier still calls this script ({len(CARRIER_PLANTS)}):")
    for label, plant in CARRIER_PLANTS:
        if check_the_carrier_still_calls_this(plant(carrier)):
            print(f"  red on                 {label}")
        else:
            print(f"  STAYED GREEN           {label}")
            failures += 1

    # ⚠️ The turn guard is state on disk, so the assertions below run against a
    # directory of their own. Without it the second run of this self-test reads
    # the first run's markers and reports that a blocking finding does not
    # block — measured, and exactly the shape of a check that passes once.
    os.environ["CLAUDE_PLUGIN_DATA"] = tempfile.mkdtemp(prefix="reply-register-self-test-")

    print("\nAsserting the answer the harness reads:")
    blocking_reply, reporting_reply = _plant_for(BLOCKS), _plant_for(REPORTS)
    blocked = answer({"last_assistant_message": blocking_reply, "prompt_id": "self-test-block"})
    if blocked.get("decision") == "block" and "additionalContext" in blocked.get(
        "hookSpecificOutput", {}
    ):
        print("  ok                     a blocking finding blocks the stop and is handed back")
    else:
        print("  FAIL                   a blocking finding did not block")
        failures += 1
    # ⛔ Asserted on the answer and not on `decision` alone. Context handed back
    # on a `Stop` is read by the writer whether or not the answer blocks, so an
    # arm that asks is an arm that costs the reply a second time -- which is why
    # each assertion below reads `hookSpecificOutput` rather than trusting that
    # an answer with no `decision` cost the reader nothing.
    again = answer({"last_assistant_message": blocking_reply, "prompt_id": "self-test-block"})
    if ("decision" not in again and "hookSpecificOutput" not in again
            and "one hand-back" in again.get("systemMessage", "")):
        print("  ok                     the same turn is handed back once only, and asks nothing twice")
    else:
        print("  FAIL                   the same turn asked for a restatement it had already had")
        failures += 1
    unguardable = answer({"last_assistant_message": blocking_reply})
    if "decision" not in unguardable and "Nothing was handed back" in unguardable.get(
        "systemMessage", ""
    ) and "additionalContext" in unguardable.get("hookSpecificOutput", {}):
        print("  ok                     a payload naming no turn asks, and says it could not guard")
    else:
        print("  FAIL                   a payload naming no turn did not say the guard was absent")
        failures += 1
    # ⛔ The two arms that report, and the whole of what the change to them is:
    # no context at all, so the turn ends, and the findings themselves in the
    # message, since that is now the only place they are said.
    reported = answer({"last_assistant_message": reporting_reply, "prompt_id": "self-test-report"})
    message = reported.get("systemMessage", "")
    if ("decision" not in reported and "hookSpecificOutput" not in reported
            and any(f in message for f in findings(reporting_reply)[1])):
        print("  ok                     a reported finding asks nothing and names itself")
    else:
        print("  FAIL                   a reported finding asked for a restatement, or named nothing")
        failures += 1
    # ⛔ A density spends nothing, asserted by the hand-back it must leave
    # available. The first shape of this change recorded a marker on every fire,
    # so a density first in a turn made the blocking finding after it report —
    # and report that the turn had had a hand-back it never had.
    spent = "self-test-density-then-block"
    answer({"last_assistant_message": reporting_reply, "prompt_id": spent})
    after = answer({"last_assistant_message": blocking_reply, "prompt_id": spent})
    if after.get("decision") == "block":
        print("  ok                     a density leaves the turn's hand-back unspent")
    else:
        print("  FAIL                   a density spent the turn's hand-back")
        failures += 1
    # ⚠️ A reporting finding on a payload naming no turn: the one shape that
    # reaches the person's message by a route where nothing was handed back and
    # nothing could be guarded either, and the arm that must not claim one.
    unguardable_density = answer({"last_assistant_message": reporting_reply})
    if ("hookSpecificOutput" not in unguardable_density
            and "hand-back" not in unguardable_density.get("systemMessage", "")):
        print("  ok                     an unguardable density asks nothing and claims no hand-back")
    else:
        print("  FAIL                   an unguardable density asked, or claimed a hand-back")
        failures += 1
    if answer({"last_assistant_message": CLEAN, "prompt_id": "self-test-clean"}) == {}:
        print("  ok                     a reply in register produces no answer at all")
    else:
        print("  FAIL                   a reply in register produced an answer")
        failures += 1
    if answer({"last_assistant_message": "   ", "prompt_id": "self-test-empty"}) == {}:
        print("  ok                     a turn carrying no reply is answered with nothing")
    else:
        print("  FAIL                   a turn carrying no reply produced an answer")
        failures += 1

    # ⛔ Every branch that asks for anything asks for this reply, not a later
    # one. The branch that fired when a density reported used to close on "the
    # next reply is written knowing them", which is a deferral stated by the
    # guard that holds the rule against deferring — and it was obeyed. It now
    # asks for nothing instead, which is the arm asserted after this one.
    print("\nAsserting no branch that asks defers the fix to a later reply:")
    branches = [
        ("handed back", dict(blocking=["a: b"], reported=[], block=True, unguarded="")),
        ("blocking, unguarded", dict(blocking=["a: b"], reported=[], block=False,
                                     unguarded="no turn is named")),
    ]
    for label, kwargs in branches:
        said = context(**kwargs)
        deferred = [phrase for phrase in DEFERRALS if phrase in said.lower()]
        if RESTATE in said and not deferred:
            print(f"  ok                     {label}: asks for this reply")
        else:
            missing = "carries no restatement" if RESTATE not in said else f"defers: {deferred}"
            print(f"  FAIL                   {label}: {missing}")
            failures += 1

    # ⛔ And the arm that asks for nothing asks for *nothing* — not a later reply
    # either. Dropping the restatement is a licence to defer unless what replaces
    # it is silence towards the writer: the message is addressed to the person,
    # and a promise about a later reply in it would be the same deferral stated
    # one reader over.
    print("\nAsserting the message to the person asks the writer for nothing:")
    for label, kwargs in [
        ("hand-back already spent", dict(blocking=["a: b"], reported=[], handed_back=True)),
        ("reported at a density", dict(blocking=[], reported=["a: b"], handed_back=False)),
    ]:
        message = told(**kwargs)
        asked = [phrase for phrase in DEFERRALS if phrase in message.lower()]
        if RESTATE not in message and not asked and "a: b" in message:
            print(f"  ok                     {label}: states the finding and asks nothing")
        else:
            why = f"defers: {asked}" if asked else (
                "asks for a restatement" if RESTATE in message else "does not state the finding")
            print(f"  FAIL                   {label}: {why}")
            failures += 1

    # ⛔ The fail-open branch, asserted rather than claimed. It was stated with
    # the binding marker in two places and exercised by nothing.
    print("\nAsserting the hook fails open and names the failure:")
    for label, payload in [("a payload that is not JSON", "not json"),
                           ("a payload that is not an object", "[1, 2]"),
                           ("an empty payload", "")]:
        captured = io.StringIO()
        code = hook(io.StringIO(payload), out=captured)
        printed = captured.getvalue().strip()
        try:
            named = "did not run" in (json.loads(printed).get("systemMessage", "") if printed else "")
        except ValueError:
            named = False
        if code == 0 and (named or printed == ""):
            print(f"  ok                     {label}: exit 0, and {'names itself' if named else 'nothing claimed'}")
        else:
            print(f"  FAIL                   {label}: exit {code}, printed {printed[:60]!r}")
            failures += 1

    if failures:
        print(f"\n{failures} assertion(s) did not hold. A check that cannot fail is not a check.")
    return 1 if failures else 0


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a != "--self-test"]
    if unknown:
        print(f"unrecognised argument(s): {' '.join(unknown)}\n\n{__doc__}")
        return 2

    if "--self-test" not in argv:
        return hook(sys.stdin)

    if self_test():
        return 1
    checks = [
        ("every property of the register is accounted for",
         check_every_property_is_accounted_for(SURFACE.read_text(encoding="utf-8"))),
        ("the carrier still calls this script",
         check_the_carrier_still_calls_this(CARRIER.read_text(encoding="utf-8"))),
    ]
    print()
    for name, problems in checks:
        print(f"  {'FAIL' if problems else 'ok  '}  {name}")
    problems = [p for _, found in checks for p in found]
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    held = sum(len(t) for t in HELD.values())
    whole = sum(1 for extent in RESIDUE.values() if extent == WHOLE)
    print(
        f"\nThe register's properties are read from the surface and wholly accounted for: "
        f"{held} held, {whole} stated as unheld, "
        f"{sum(1 for e in RESIDUE.values() if e == PARTIAL)} held in part."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
