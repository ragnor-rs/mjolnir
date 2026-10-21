#!/usr/bin/env python3
"""Hold a role's reply to leaving no work unfinished.

The surface's first rule binds every artifact a role produces, and the reply is
the one artifact no later gate reads: no commit, no body, no thread, so work
named in a session and not done escapes every check after it. That is what this
holds, on the one artifact whose only reader is the person running the role.

⛔ **It holds no property of prose, by the ruling of 2026-10-20.** Style is a
rule the surface states and a session loads, never a check -- measured on this
check's own record, where 30 hand-backs carried 3 true findings and every one of
those 3 was an offer standing in for the work. What the five style arms cost was
a re-read each; what they held was nothing, since the channel that reported them
never reached the writer at all.

It runs as a `Stop` hook, which is the only place the finished reply exists: the
harness hands the hook `last_assistant_message`, so nothing here parses a
transcript or guesses at what was sent.

⚠️ **What this arm does not catch, and every limit it has, are recorded once in
`docs/single-source-of-truth.md` § The reply defers nothing.** This docstring
deliberately does not restate them: two prose copies of a limit are the defect
this repository exists to delete, and nothing holds a docstring to a document.

⛔ **The hand-back asks for the work and never for text.** A finding that named a
parked sentence and then asked for that sentence replaced had the writer delete
the evidence rather than do the work -- measured, 3 real parkings caught and no
work item moved. The patterns are grammar and live here.

Usage:
    check_reply_defers_nothing.py              read a hook payload on stdin, answer on stdout
    check_reply_defers_nothing.py --self-test  assert the arm reddens on each planted parking,
                                               that each carved sense stays green, and that the
                                               carrier still calls this script
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

# The rule this holds, cited rather than restated: the surface's first rule,
# on one artifact of it. ⛔ Not § 8 — nothing of that table is read here any
# more, and a citation naming it would point the reader at a register this
# check stopped having an opinion about.
CITATION = "schema § Nothing is deferred"

# What a hand-back asks for. ⛔ **The work, and no text at all.** This replaced
# two asks that each named prose -- a span and its replacement, or the reply
# re-sent -- and both were wrong in the same direction: the cheapest answer to
# *replace this sentence* is to delete the sentence that named the parked work,
# which is the finding's own evidence rather than its subject. Measured on this
# check's record: 3 real parkings caught, 3 sentences rewritten, no work item
# moved.
#
# ⚠️ It asks for the same turn, and promises nothing about a later reply: a
# branch telling the writer the *next* reply would be better would be a deferral
# stated by the guard that holds the rule against deferring. `--self-test` holds
# the asking answer to carrying this sentence and none of the four below.
#
# ⚠️ `DEFERRALS` is a closed list, and it is the *quoting* weakness this
# repository rules out elsewhere -- safe only because what it sweeps is the
# string authored above rather than arbitrary text.
ASK = ("Do the work in this turn, under the current branch, pull request and item — or ask the "
       "one question that blocks it, with its options and what each costs. ⛔ The reply just "
       "sent is not rewritten and no span is replaced: the sentence that named the work stands, "
       "and what comes back is what the work did. Where the finding is wrong, one sentence "
       "naming why nothing is parked is the whole answer.")
DEFERRALS = ("the next reply", "a later reply", "written knowing", "next time")

# The carrier that calls this script, and the event it registers for. Grammar:
# the path and the event name. ⛔ Held rather than assumed -- the carrier naming
# a script that is not this one, or an event that is not the one carrying a
# finished reply, leaves the gate green and the hook silently dead, which is the
# failure the workflow exists to catch.
CARRIER = Path(__file__).resolve().parent.parent / "hooks" / "hooks.json"
CARRIER_EVENT = "Stop"

# --- the grammar -----------------------------------------------------------
#
# A form rather than a judgement, which is what makes a forbidding check sound.
# ⚠️ That was the test five style arms failed: a density over a reply's prose is
# a form too, and it still answered a question about whether the prose was any
# good -- which is the ruling behind this file carrying one arm.


# Work the reply names and the turn does not do. The rule is § Nothing is
# deferred's and is not restated here; what is written here is the grammar of the
# forms it was measured escaping through, which are all first person or addressed
# to the reader -- a reply parks work by promising it, offering it, or excusing
# its absence, never by describing somebody else's.
#
# ⛔ **The floor is one and it blocks.** A single parked sentence is the whole
# violation -- there is no density to reach, because parking is an act and not a
# texture -- and the reply is the cheapest place in the loop to commit one: no
# commit, no body, no thread, so no gate after it sees what was named.
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
# `left` has it for the bare word, which is this repository's ordinary English
# for what a process or a merge did -- *three trees left behind*. ⛔ **It had
# that carve-out in the third person only.** One alternative
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
    # ⛔ **`unsaved` is deliberately *not* in this list, and that was measured
    # rather than assumed.** A reply carrying *## Left deliberately unsaved* over
    # a finding it declined to file passed this arm, which reads as a hole. It is
    # not one: `deliberately unsaved` is the **save role's own ruled section** —
    # the convention asks a save to say what it left unsaved — and the sweep
    # found it in **9** of this project's replies in exactly that sense (*##
    # Deliberately unsaved*, *Deliberately unsaved: nothing about the ordering*,
    # *## What was left unsaved deliberately*). An artifact deliberately not
    # written is not work not done, and no grammar separates the two here. ⚠️ So
    # the parking that reply carried is missed by rule, on the direction this
    # whole arm states: a reworded parking passes and a finding is never
    # invented.
    r"|\bdeliberately (?:absent|omitted|skipped|unfixed|undone|untouched|unfinished|incomplete)\b"
    r"|\bdeliberately (?:not|never) "
    r"(?:done|fixed|built|run|implemented|wired|added|filled|tested|touched|handled|covered)\b"
    # `stated plainly`: a gap stated in place of being closed. ⚠️ Not the plain
    # statement § 8 asks for, and not what is stated plainly *about* a gap.
    # ⛔ The second form here read a cost and `stated plainly` in one line as a
    # parking, and the corpus sweep found it on *## The cost of saying no,
    # stated plainly* -- a heading doing exactly what § 8 asks of a reply. A
    # cost named beside the promise to state it is the register, not a parking,
    # so only the form that says a gap was stated *in place of* closing it is
    # matched, and a parking reworded past that is missed by rule.
    r"|\bstated plainly (?:rather than|instead of)\b"
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
    r"\b(?:undone|unfixed|unaddressed|unfinished)\b"
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
    # ⛔ **A filing that did not happen is deliberately not matched**, and this
    # was measured against the corpus rather than reasoned about. The form was
    # written -- *no issue was filed* and its first-person variant -- and the
    # sweep reddened **6** replies that are honest reports: *No item was filed —
    # #70 was reopened and edited*, *No work item filed: found and fixed in the
    # same pass*, *no issues filed, no labels, no bodies edited*. Declining a
    # filing is what the measure-it rule **asks for** when the pass fixed the
    # thing, so the absence of a filing carries no parking by itself and the
    # reason that would separate the two is open-ended prose. ⚠️ Matching it
    # would invent findings, which is the one direction this arm may not fail in.
    # ⛔ **The marker, and only in the casing that is a marker.** `re.I` over the
    # whole pattern made this match the ordinary English noun -- `todo queue`,
    # `todo list`, `the todos` -- and the first of those was measured on
    # 2026-10-20, on a reply reporting that the queue was *empty*, which is the
    # absence this rule asks for rather than a parking. The convention the rule
    # names is an all-capitals source marker, so the casing is the grammar: a
    # local flag turns the enclosing `re.I` off for this alternative alone.
    r"|\b(?-i:TODO)\b",
    re.I,
)
PARKED_FLOOR = 1

# ⛔ **Three senses carved out by measurement rather than by argument**, over
# 2,713 assistant messages in this project's own transcripts that carried text
# and no tool call. ⚠️ **That is not the corpus of the artifact this arm holds**,
# which it was read as being: a `Stop` payload carries the last reply of a turn,
# so a message followed by a tool call is never in one, and most of a session's
# text is exactly that. The split is measured in the document, and the sweep's
# verdicts below stand either way — a sense carved out is carved out whether or
# not the reply it was measured on could have been handed back.
#
# Over that set, 99 spans matched across 27 distinct forms, and the majority are
# the acts the rule is for: 39 `say the word`, the offers, the sections of work
# named and not done. ⚠️ **What the sweep found instead is that
# four forms carry a second sense this repository writes constantly**, and each
# carve-out below is read around the match rather than over the reply.
#
#   - **A citation of another artifact's heading.** `"What is left"` is a section
#     of one work item's body, cited in three replies that then falsified it. A
#     double-quoted span is not the writer's own text, which is the carve-out a
#     code span and a block quote already have, so it is blanked before matching.
#     ⛔ **A cited heading, and not every quoted span.** The first shape blanked
#     anything in double quotes, which greened *the density arm is a "follow-up"
#     and not in this change* -- a parking whose writer scare-quoted the ruled
#     word. So the span must read as a title: more than one word, and opening on
#     a capital or an item reference, which every citation measured here does and
#     no scare-quoted ruled phrase does. ⚠️ A lowercase heading cited this way
#     reddens, and the sweep is what would find it.
#   - **A negation.** *Nothing was stashed, moved or left out*, *Nothing is left
#     open from this session's work*, *not questions left open* — four replies
#     reddened for stating the absence the rule asks for. ⚠️ Bounded to the
#     negator's own clause: a parking after a comma or a semicolon is a parking,
#     and *I did not finish it, so next steps:* stays red.
#   - **§ 10's own instruction, obeyed.** *Say what is left to remove and where*
#     is what the surface tells a role that cannot delete the tree it stands in,
#     and six replies reddened for carrying it out. The same for a scope stated
#     by declaration: *out of scope by that project's declaration* describes a
#     mechanism where the bare form reads as a writer's excuse.
#
#   - **Work the surface reserves to the person.** *It isn't my claim, so I
#     haven't touched it*, *"ok" is not authorization to delete, so I have not
#     touched it*, *that document is the close-out role's, so I have not touched
#     it* — five replies reporting the one thing a role is required to do, which
#     is to stop. ⚠️ Read with the denial that governs it: the carve-out needs an
#     earlier clause in the same sentence denying the writer's ownership or
#     authority, so the measured parking — *two things that follow, which I
#     haven't touched* — carries no denial and stays red.
#   - **An artifact's own decisions, described.** *The decisions the item left
#     open*, *a question my own notes had left open*: the subject is the item or
#     the notes, not the writer. ⛔ Read with its subject, and the subject must
#     not be the writer: *the two items I left open remain open* is a parking and
#     stays red, which is why the first person is excluded from the gap rather
#     than the noun alone being matched.
QUOTED = re.compile(
    r"\"(?=[A-Z#\d])[^\"\n]{0,80}\s[^\"\n]{0,80}\""
    r"|“(?=[A-Z#\d])[^”\n]{0,80}\s[^”\n]{0,80}”"
)
# ⚠️ The two negators are bounded differently, and the measured sentences are why:
# *nothing was stashed, moved or left out* coordinates a list across commas, while
# a bare `not` carries no such list and a comma after it starts a new clause --
# *I did not finish it, so next steps:* is a parking and stays red. So `nothing`
# crosses a comma but never a clause word, and `not` does not cross either.
NEGATED = re.compile(
    r"\b(?:nothing|none)\b(?:(?!\b(?:so|but|then|though|however|while)\b)[^.;:\n]){0,45}$"
    r"|\bnot\b[^.,;:\n]{0,35}$",
    re.I,
)
CARVED = re.compile(
    # § 10's own instruction, in the three wordings the corpus carries: the
    # phrase with its object, the phrase as a heading with the *and where* the
    # surface asks for, and the role reporting it because it cannot act
    r"what(?:'?s| is) left to (?:remove|delete)\b"
    r"|what(?:'?s| is) left,? and where\b"
    r"|\b(?:report|reports|say|says|name|names|state|states)s? ?"
    r"what(?:'?s| is) left\b"
    r"|\bout of scope by\b"
    # what governs *I have not touched it*, in an earlier clause of the same
    # sentence: ownership or authority denied, or the thing attributed to another
    # owner outright -- *that document is the close-out role's* denies nothing
    # and reserves the work just as firmly
    r"|(?:(?:is ?n'?t|is not|was not|are not|'s not) "
    r"(?:my|mine|authoriz\w*|authoris\w*|part of)"
    r"|(?:is|was) (?:the )?[^.\n]{0,25}?(?:role|session|item|project|reviewer|author)'s"
    r"|\bbelongs to\b)"
    r"[^.\n]{0,60}?\bI have(?:n'?t| not) touched\b"
    # the subject of *left open* being an artifact rather than the writer
    r"|\b(?:items?|issues?|bodies|body|notes?|sections?|changes?|pull requests?|threads?|#\d+)\b"
    r"(?:(?!\bI\b)[^.\n]){0,20}?(?:had |has |have )?(?:left|leaves) open\b"
    # ⛔ What the surface reserves to the person, handed over as it requires. § 10
    # says a role cannot delete the tree it stands in, and the priority rule says
    # a role never derives a priority -- so *left for you | the tree and its
    # local branch* and *left for you per the derivation rule* carry out a rule
    # rather than parking the writer's work. ⚠️ Matched by the thing handed over,
    # which is a closed list, and not by the wording: a parking that names a tree
    # in the same sentence passes, which is this list's ruled direction.
    r"|\b(?:left|leaving|leave) (?:it |them |that |this )?(?:for|to) you\b[^.\n]{0,70}?"
    r"\b(?:tree|worktree|branch|priority|label|merge|claim)\b"
    r"|\b(?:tree|worktree|branch|priority|label|merge|claim)\b[^.\n]{0,70}?"
    r"\b(?:left|leaving|leave) (?:it |them |that |this )?(?:for|to) you\b"
    # the passive sense of *left out*: what a process or a mishap did, where the
    # parking sense is the writer's own omission -- *left out of the commit*
    r"|\bleft out of\b"
    # a state described rather than handed on: *the queue left as the next
    # session reads it*, where the parking sense hands the work to that session
    r"|\bleft as the next\b[^.\n]{0,25}?\b(?:reads?|sees?|finds?|will read)\b"
    # ⛔ **`left open` read with its predicate, which is how a landing report
    # describes what it settled.** Measured on a reply reporting #65: *the two
    # questions the six wordings left open are answered* was handed back, on the
    # span `stions the six wordings left open are answered`. The clause states a
    # resolution and the resolving verb is in it. ⚠️ The subject carve-out above
    # could not reach it — that one matches a **closed noun list** before the
    # phrase, and `wordings` is not in it, which is the whack-a-mole this form
    # replaces: the predicate is the signal, not the noun. ⛔ Bounded to the same
    # clause, so *the questions left open are answered, and three more are not*
    # still reddens on its second clause.
    # ⛔ `in` was written here as *the fix is in* and **withdrawn**: it carved
    # *the two questions left open are in #99* green, which is a deferral to
    # another item and the plainest parking there is. The resolving verb has to
    # say the thing is answered, not where it went.
    r"|\bleft open[^.,;:\n]{0,30}?\b(?:are|is|were|was|have been|has been|now)\s+"
    r"(?:all )?(?:answered|settled|resolved|closed)\b"
    # ⚠️ The verb-first gap is wider than the predicate form's, measured rather
    # than guessed: *answered both questions the six carve-outs left open* puts
    # 34 characters between them, and the first bound written here was 30, so the
    # green plant reddened. It stays bounded by clause punctuation either way.
    r"|\b(?:answered|settled|resolved|closed)\b[^.,;:\n]{0,45}?\bleft open\b",
    re.I,
)

# ⛔ The one ruled form that is read with its answer rather than as a span. A
# section of open items is a finding where it lists any, and the gate on the
# change's body already holds the same section to being answered with one
# string and nothing else -- so a reply carrying that answer states that it
# parked nothing, and handing it back is the false red this arm is being
# narrowed to stop. The heading is matched on its text at any level, and the
# label form carries its answer on the same line.
#
# ⛔ **What counts as that answer is an absence stated, not one spelling of it.**
# The first shape took the body gate's string exactly -- the bare word `None.`
# and nothing else -- on the reasoning that a reply and a body answering one
# question differently would be two conventions for one rule. ⚠️ **That
# reasoning was wrong about which question is being asked.** A pull request body
# is a form a gate parses, so one string there is a schema; a reply is prose a
# person reads, and the same clause carries its reason -- *none that this turn
# owns*, *nothing is opened or carried by this turn*. Measured on 2026-10-20: a
# reply answering the section with its own standing state was handed back, and
# every answer but the bare word reddened.
#
# So the answer is read as a clause that opens by denying there are any, and a
# parking that follows such a clause is caught by the forms above rather than
# here -- *none of it is done, so next steps:* stays red on `next steps`.
OPEN_ITEMS_SECTION = re.compile(
    r"^\s{0,3}(?:#{1,6}\s*|(?:\*\*|__)\s*)?open items?\s*(?:\*\*|__)?"
    r"\s*(?::\s*(?P<answer>\S.*?))?\s*$",
    re.I,
)
NO_OPEN_ITEMS = re.compile(r"^\s*(?:[-*+]\s+)?(?:none|nothing|no)\b", re.I)

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
QUOTE = re.compile(r"^\s*>")


# --- reading the reply -----------------------------------------------------


def prose(reply: str) -> list[str]:
    """The lines of a reply that are prose, in order.

    Code goes whole — fenced blocks by their marker, indented blocks by their
    indent — and inline code spans are removed from the lines that survive. A
    quoted line is not the writer's own text, so it is not held against them.

    ⛔ **A table row is prose here.** It was a parameter while five arms read
    rows differently; with one arm left there is one answer, and that answer is
    yes: a `verdict` cell saying *next steps* parks exactly what a sentence
    would. A flag whose only caller always passed the same value is weight
    nothing carries.

    ⚠️ The indent rule over-reaches in the safe direction: a list item's
    four-space continuation line is read as code and checked by nothing. That
    is a finding missed rather than a finding invented, which is the right way
    round for a check that blocks.
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
        out.append(CODE_SPAN.sub(" ", line))
    return out






# --- the checks ------------------------------------------------------------
#
# Each returns a list of findings. A finding is one sentence naming the property
# and what in the reply failed it, because the reply is what gets restated and a
# finding that does not say where is a finding nobody can act on.














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
    lines = prose(reply)
    found = []
    for index, line in enumerate(lines):
        # ⚠️ Blanked to the same length, so a reported span still lines up with
        # the line the writer wrote.
        read = QUOTED.sub(lambda m: " " * len(m.group(0)), line)
        for match in PARKED.finditer(read):
            if NEGATED.search(read[:match.start()]):
                continue
            if any(c.start() <= match.start() and c.end() >= match.end()
                   for c in CARVED.finditer(read)):
                continue
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
        f"Completeness: the reply names work this turn does not do ({CITATION}) — "
        + "; ".join(repr(s) for s in shown)
        + f".{more} The work goes under the current branch, pull request and item, or the one "
        "question that blocks it is asked instead."
    ]


# The one thing held here, and the rule it holds. ⛔ **One arm, and no table of
# properties read out of the surface.** While five style arms stood beside this
# one, the surface's own property table was read at run time so that a row added
# there reddened until somebody held it or said why not. With nothing but this
# arm left, that accounting had nothing to account for: the row this holds is the
# only one any check reads, and the rest of that table is a rule a session loads.
HELD = [("nothing is parked", check_nothing_is_parked)]


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


def findings(reply: str) -> list[str]:
    """Every finding against one reply.

    ⚠️ One list and not two. While five style arms stood beside this one the
    answer sorted findings into what hands the turn back and what only reaches
    the person, because a density was not worth a re-read. With one arm left,
    every finding it can produce is an act rather than a texture, and the split
    had one side permanently empty.
    """
    out: list[str] = []
    for _, test in HELD:
        out.extend(test(reply))
    return out


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
        root = os.path.join(tempfile.gettempdir(), f"reply-defers-nothing-{os.getuid()}")
    seen = Path(root) / "reply-defers-nothing-turns"
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
    found = findings(reply)
    if not found:
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
        handed_back, unguarded = already_blocked(turn, record=True)
        block = not handed_back

    # ⛔ Asked of the writer only where a hand-back is warranted *and* the work is
    # still owed: a spent hand-back has had its ask, and that reaches the person
    # instead.
    if not (block or unguarded):
        return {"systemMessage": told(found, handed_back)}

    out: dict = {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": context(found, block, unguarded),
        }
    }
    if block:
        out["decision"] = "block"
        # ⚠️ What was asked for is named, because *handed back* alone reads as the
        # whole reply coming again — which is what this used to mean and is now
        # the one thing the ask forbids.
        out["reason"] = (
            f"The reply names work this turn does not do ({CITATION}). "
            + "; ".join(dict.fromkeys(f.split(":", 1)[0] for f in found))
            + " — handed back once, for the work and not for any text."
        )
    else:
        out["systemMessage"] = (
            f"Reply defers nothing: {len(found)} finding(s) against {CITATION}. "
            f"Nothing was handed back: {unguarded}."
        )
    return out


def told(found: list[str], handed_back: bool) -> str:
    """What the person reads when the writer is asked for nothing.

    The findings themselves and not a count of them: this is the only place they
    are said on this route, so a message carrying the number alone would report
    that work was parked without saying which.
    """
    lines = [f"Reply defers nothing: {len(found)} finding(s) against {CITATION}."]
    lines += [f"  - {f}" for f in found]
    if handed_back:
        lines.append("  Nothing more is asked: this turn has had its one hand-back.")
    return "\n".join(lines)


def context(found: list[str], block: bool, unguarded: str = "") -> str:
    """What the writer is asked for, on the two answers that ask for anything.

    ⛔ **One ask, and it names no text.** There were two — a span and its
    replacement, or the reply re-sent — chosen by a reach declared per arm. Both
    are gone with the arms that needed the choice, and the reason is measured
    rather than aesthetic: asked to replace the sentence that named parked work,
    a writer deletes the sentence. The work is what is owed, so the work is what
    is asked for, and `--self-test` asserts that neither retired sentence can
    reach this string again.

    ⛔ There is also no branch that promises a later reply. One closed on *the
    next reply is written knowing them*, which is a deferral stated by the guard
    that holds the rule against deferring.
    """
    lines = [f"The first rule reaches a role's own reply: {CITATION}. Work this reply names "
             "and this turn does not do:"]
    lines += [f"- {f}" for f in found]
    if block:
        lines.append(f"This turn is handed back once only; a second reply is not blocked. {ASK}")
    else:
        lines.append(
            f"Nothing is blocked, and not because these findings are weak: {unguarded}. {ASK}"
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
                f"Reply defers nothing: the check did not run ({type(error).__name__}), so "
                "this reply was held to nothing."
            )
        }), file=out)
        return 0
    if answered:
        print(json.dumps(answered), file=out)
    return 0


# --- the planted violations ------------------------------------------------
#
# One per form the arm reads, and one per sense carved out of it -- the green
# side being the half a narrowing is only asserted by: a check that reddens on a
# ruled phrase inside a fenced block is not the check this file claims to carry.

CLEAN = (
    "Three relations were added and one was refused.\n\n"
    "| edge | why |\n|---|---|\n| #6 ← #77 | setup cannot generate a key it does not know |\n\n"
    "The refusal is in `tools/check_single_source.py`, which reads the anchor set at run time.\n"
)

REDDENS = [
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
    # ⚠️ The red side of each sense carved out by the transcript sweep: a negator
    # in an earlier clause, and a section of work the sweep's own corpus showed
    # is a parking as often as it is a report.
    # ⛔ The red side of the carve-out this change adds, which is what stops it
    # being a hole: a deferral *to another item* uses the same phrase and the
    # same copula, and the token that greened it was withdrawn for this.
    ("nothing is parked", "the phrase with a destination rather than a resolution",
     "The two questions left open are in #99.\n"),
    ("nothing is parked", "a parking after a negator's own clause ends",
     "I did not finish the second arm, so next steps: wire the carrier.\n"),
    ("nothing is parked", "the writer's own work handed over, naming nothing the surface reserves",
     "The narrowing is in. The density arm is left for you to finish.\n"),
    ("nothing is parked", "the writer's own omission, where the passive sense is carved out",
     "The sweep is in, and I left out the two arms it found.\n"),
    ("nothing is parked", "a gap stated in place of being closed, which is the ruled form",
     "The second arm's cost is stated plainly rather than fixed.\n"),
    # ⛔ The marker alternative had no plant at all until its casing became
    # grammar, so nothing asserted it fired. Both sides of that casing are
    # planted: this one, and `a queue of them named in ordinary English` below.
    ("nothing is parked", "the source marker, in the casing the convention names",
     "The guard is wired and its plants are green. TODO: the carrier.\n"),
    ("nothing is parked", "a ruled word the writer scare-quoted, which is still the writer's",
     "The density arm is a \"follow-up\" and not in this change.\n"),
    ("nothing is parked", "work not done, with no denial of ownership before it",
     "The carrier is wired. Two things that follow, which I haven't touched: the skill's own "
     "wording, and the ignore entry.\n"),
    ("nothing is parked", "work named as still open, with no negation anywhere",
     "The first arm is narrowed. The two items I left open remain open.\n"),
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
    # ⚠️ Each sentence below is one this project's own replies have in fact been
    # reddened on, read off 2,713 of them: a heading cited, an absence stated,
    # the surface's own instruction carried out, a scope declared, and the two
    # words a parked state is no longer read with.
    # ⛔ The false red this change was measured on, and the sense beside it: a
    # landing report names what it settled, so it names what had been open.
    ("nothing is parked", "a resolution stated with the phrase, the noun carve-out cannot reach",
     "The two questions the six wordings left open are answered: a manifest name may not appear "
     "in a carrier's text.\n"),
    ("nothing is parked", "the same resolution with the verb first",
     "The section answered both questions the six carve-outs left open.\n"),
    # ⛔ The green side of the two forms this change wrote and then **withdrew**,
    # kept as plants so the withdrawal is asserted rather than remembered: both
    # were reddened by the corpus and both must stay green.
    ("nothing is parked", "a filing declined because the pass fixed it instead",
     "No issue was filed, because this pass measured the defect and the fix is in this change.\n"),
    ("nothing is parked", "a filing declined because the owning item was reopened",
     "Done, in full. No item was filed — #70 was reopened and edited.\n"),
    ("nothing is parked", "the save role's own ruled section, naming an artifact not written",
     "The plan is stamped and memory is written.\n\n## Deliberately unsaved\n\n"
     "Nothing about the ordering, which no landing touched.\n"),
    ("nothing is parked", "another item's section heading, cited and then falsified",
     "The snapshot was stale, which falsifies #27's \"What is left\" wholesale.\n"),
    ("nothing is parked", "the absence the rule asks for, stated",
     "The tree was clean: nothing was stashed, moved or left out.\n"),
    ("nothing is parked", "a section's contents corrected, with the parking negated",
     "That section listed the calls made in this pass, not questions left open.\n"),
    ("nothing is parked", "§ 10's own instruction to a role that cannot delete its own tree",
     "I cannot remove the tree this session stands in, so this says what is left to remove and "
     "where.\n"),
    ("nothing is parked", "a scope stated by declaration, which is a mechanism and not an excuse",
     "Those carriers are out of scope by declaration rather than by measurement.\n"),
    ("nothing is parked", "the runs a review left red, which is a count and not an omission",
     "One review with four comments left six runs, all red on the same unresolved threads.\n"),
    ("nothing is parked", "items that needed no edit, reported",
     "#51, #52 and #53 already carried the label and were left untouched.\n"),
    ("nothing is parked", "a role stopping where the surface reserves the work to the person",
     "It isn't my claim, so I haven't touched it: the branch is stale rather than orphaned.\n"),
    ("nothing is parked", "the same, where what is denied is authority rather than ownership",
     "An acknowledgement is not authorization to delete, so I have not touched it.\n"),
    ("nothing is parked", "another role's artifact, reported as not this pass's to edit",
     "That document is the close-out role's, so I have not touched it.\n"),
    ("nothing is parked", "§ 10's handover of the tree a session cannot delete",
     "| Left for you | the tree and its local branch, with the command above |\n"),
    ("nothing is parked", "the same instruction as a heading, with the surface's own *and where*",
     "## What is left, and where\n\nThe tree this session stands in, and its local branch.\n"),
    ("nothing is parked", "a role reporting the remainder because it cannot act on it",
     "This session is pinned to the tree, so I report what is left rather than a release that "
     "did not happen.\n"),
    ("nothing is parked", "a priority the derivation rule reserves to the person",
     "Issue #54 is filed with a topical label only, left for you per the derivation rule.\n"),
    ("nothing is parked", "the passive sense of a thing omitted by a process",
     "Those edits were verified green by every local check and left out of the commit.\n"),
    ("nothing is parked", "a cost named beside the promise to state it, which is the register",
     "## The cost of saying no, stated plainly\n\nThe queue loses two days.\n"),
    ("nothing is parked", "a queue described in the state the next session will read",
     "No row is re-ranked, and the queue above left as the next session reads it.\n"),
    ("nothing is parked", "an item's own decisions, described rather than parked",
     "The decisions the item left open are the two the gate names.\n"),
    ("nothing is parked", "a question an artifact of the writer's had left open, then answered",
     "One finding resolved a question my own notes had left open, and the correction is in.\n"),
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
    # ⚠️ The two false reds measured on 2026-10-20, in the shapes they were
    # handed back in. Each is the green side of a narrowing made the same day,
    # and each fails if its narrowing is reverted — asserted by reverting it,
    # not by reading the pattern.
    ("nothing is parked", "a queue of them named in ordinary English, reported empty",
     "The sweep is in and the plants are green. Todo queue is empty.\n"),
    ("nothing is parked", "the same section answered with an absence that carries its reason",
     "The guard is wired.\n\n## Open items\n\nNone that this turn owns.\n"),
    ("nothing is parked", "the same answered as a sentence rather than as the bare word",
     "The guard is wired.\n\n## Open items\n\nNothing is opened or carried by this turn.\n"),
    ("nothing is parked", "a reply that does the work and asks nothing",
     CLEAN),
]


# --- the plants against the carrier ----------------------------------------
#
# ⛔ A plant may not name the content it plants into. The first draft spelled out
# a whole row of a table and a subsection's heading text, so rewording either
# made `str.replace` a no-op: the plant planted nothing, the self-test printed
# STAYED GREEN, and the workflow — whose only step this is — failed on an edit
# that was not a defect.

CARRIER_PLANTS = [
    ("a carrier that is not valid JSON", lambda text: text.rstrip()[:-1]),
    ("a carrier registering no handler for the event",
     lambda text: text.replace(f'"{CARRIER_EVENT}"', '"PreToolUse"')),
    ("a carrier calling a script that is not this one",
     lambda text: text.replace("check_reply_defers_nothing.py", "check_something_else.py")),
    ("a carrier whose expansion of the plugin root is mistyped",
     lambda text: text.replace("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOTS")),
]


def _plant_for_a_finding() -> str:
    """A planted reply that produces a finding.

    ⚠️ Chosen by what `findings()` answers rather than by position in `REDDENS`,
    so inserting a plant cannot silently repoint the assertions about the answer
    at a different reply.
    """
    for _, _, reply in REDDENS:
        if findings(reply):
            return reply
    raise AssertionError("no planted reply produces a finding")


def self_test() -> int:
    """Assert the arm reddens where it must, stays green where it must, and that
    the answer asks for the work rather than for text.

    ⛔ The retired asks are asserted **absent**, by their own opening words. A
    check that merely stopped calling them would pass a file that still carried
    one, and the whole ruling behind this change is that no answer here asks for
    prose.
    """
    failures = 0

    print("Asserting each planted parking reddens:")
    for name, label, reply in REDDENS:
        found = findings(reply)
        if found:
            print(f"  ok                     {label}")
        else:
            print(f"  FAIL                   {label}: nothing fired on {name}")
            failures += 1

    print("\nAsserting each carved sense stays green:")
    for name, label, reply in STAY_GREEN:
        found = findings(reply)
        if not found:
            print(f"  ok                     {label}")
        else:
            print(f"  FAIL                   {label}: {found[0][:110]}")
            failures += 1

    print("\nAsserting the answer the harness reads:")
    # ⛔ A fresh marker directory, because the one-hand-back guard keeps state on
    # disk: a self-test sharing it with a previous run reads its own turn id as
    # already spent, and the first assertion below then fails on a check that is
    # working. Measured — this line was dropped once and that is exactly what it did.
    os.environ["CLAUDE_PLUGIN_DATA"] = tempfile.mkdtemp(prefix="reply-defers-nothing-self-test-")
    reply = _plant_for_a_finding()
    blocked = answer({"last_assistant_message": reply, "prompt_id": "turn-A"})
    said = blocked.get("hookSpecificOutput", {}).get("additionalContext", "")
    if blocked.get("decision") == "block" and ASK in said:
        print("  ok                     a finding blocks the stop and asks for the work")
    else:
        print(f"  FAIL                   a finding did not block, or did not ask: {blocked}")
        failures += 1

    # ⛔ Asserted on the answer and not on `decision` alone: context handed back
    # continues the turn whether or not the answer blocks, so an arm that stopped
    # blocking but kept injecting would still cost the reader a reply.
    again = answer({"last_assistant_message": reply, "prompt_id": "turn-A"})
    if ("decision" not in again and "hookSpecificOutput" not in again
            and "one hand-back" in again.get("systemMessage", "")):
        print("  ok                     the same turn is handed back once only, and asks nothing twice")
    else:
        print(f"  FAIL                   the same turn was handed back twice: {again}")
        failures += 1

    unguardable = answer({"last_assistant_message": reply})
    if ("decision" not in unguardable
            and "Nothing was handed back" in unguardable.get("systemMessage", "")
            and ASK in unguardable.get("hookSpecificOutput", {}).get("additionalContext", "")):
        print("  ok                     a payload naming no turn asks, and says it could not guard")
    else:
        print(f"  FAIL                   an unguardable payload answered wrong: {unguardable}")
        failures += 1

    print("\nAsserting no answer asks for text, and none defers:")
    branches = [
        ("a hand-back", dict(found=["Completeness: a"], block=True)),
        ("an unguarded finding", dict(found=["Completeness: a"], block=False,
                                      unguarded="the guard could not keep state")),
    ]
    # The opening words of the two retired asks. ⚠️ Their own strings, so a
    # reworded reinstatement passes — what catches that is the ASK assertion
    # above, which holds the answer to carrying this one and nothing else.
    retired = ("name the span above", "give the text that stands in its place",
               "Re-send this reply corrected", "the reply is not sent again")
    for label, kwargs in branches:
        text = context(**kwargs)
        asks_text = [phrase for phrase in retired if phrase in text]
        defers = [phrase for phrase in DEFERRALS if phrase in text.lower()]
        if ASK in text and not asks_text and not defers:
            print(f"  ok                     {label}: asks for the work, no text, no deferral")
        else:
            why = (f"asks for text: {asks_text}" if asks_text
                   else f"defers: {defers}" if defers else "does not carry the ask")
            print(f"  FAIL                   {label}: {why}")
            failures += 1

    print("\nAsserting a reply in register produces no answer at all:")
    if not answer({"last_assistant_message": CLEAN, "prompt_id": "turn-B"}):
        print("  ok                     a clean reply is answered with nothing")
    else:
        print("  FAIL                   a clean reply produced an answer")
        failures += 1
    if not answer({"prompt_id": "turn-C"}):
        print("  ok                     a turn carrying no reply is answered with nothing")
    else:
        print("  FAIL                   a turn with no reply produced an answer")
        failures += 1

    print("\nAsserting the carrier still calls this script on the event carrying a reply:")
    carrier = CARRIER.read_text()
    if not check_the_carrier_still_calls_this(carrier):
        print("  ok                     the carrier as it stands registers this script")
    else:
        for finding in check_the_carrier_still_calls_this(carrier):
            print(f"  FAIL                   {finding}")
            failures += 1
    for label, plant in CARRIER_PLANTS:
        if check_the_carrier_still_calls_this(plant(carrier)):
            print(f"  ok                     {label}")
        else:
            print(f"  FAIL                   {label}: stayed green")
            failures += 1

    print("\nAsserting the hook fails open and names the failure:")
    out = io.StringIO()
    code = hook(io.StringIO("not json at all"), out)
    printed = out.getvalue()
    if code == 0 and "did not run" in printed:
        print("  ok                     a payload it cannot read is answered, not raised")
    else:
        print(f"  FAIL                   a broken payload answered {code}: {printed[:120]}")
        failures += 1

    print()
    if failures:
        print(f"{failures} assertion(s) failed.")
        return 1
    print("All assertions held.")
    return 0


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a != "--self-test"]
    if unknown:
        print(f"unrecognised argument(s): {' '.join(unknown)}\n\n{__doc__}")
        return 2

    if "--self-test" not in argv:
        return hook(sys.stdin)

    if self_test():
        return 1
    problems = check_the_carrier_still_calls_this(CARRIER.read_text(encoding="utf-8"))
    print()
    print(f"  {'FAIL' if problems else 'ok  '}  the carrier still calls this script")
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    # ⛔ The run prints what it holds and what it does not, because the second
    # half is the part that reads later as coverage. One arm is held here; every
    # other property of a reply is a rule the surface states and a session
    # loads, and no check in this tree reads one.
    print(
        f"\n{len(HELD)} arm held: work the reply names and the turn does not do. "
        f"{len(REDDENS)} planted parkings redden, {len(STAY_GREEN)} carved senses stay green. "
        "No property of prose is held by anything here."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
