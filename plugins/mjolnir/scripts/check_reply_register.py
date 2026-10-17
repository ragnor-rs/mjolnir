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
# unrelated legitimate mappings in one sentence -- read as a chain. The operand
# between the two arrows is what separates them: a chain's is one or two tokens,
# and two mappings in a sentence have a clause between them.
ARROW = r"(?:→|⇒|->|=>)"
CHAIN = re.compile(ARROW + r"\s*\S+(?:\s+\S+)?\s*" + ARROW)

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
        for chain in CHAIN.finditer(line):
            findings.append(
                f"Length: text is compressed into an arrow chain — {chain.group(0).strip()[:60]!r}. "
                "Shortening is by selection, never by compression."
            )
    # ⚠️ Three is enough to act on and a wall of them is not, but the cap is
    # reported rather than silent: a bounded finding list that reads as the
    # whole truth is the same defect as a check that holds nothing.
    if len(findings) > 3:
        dropped = len(findings) - 3
        findings = findings[:3] + [
            f"Length: {dropped} further compressed line(s) are not listed; the whole reply "
            "needs restating rather than patching line by line."
        ]
    return findings


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


# Which property of the surface's table each check holds, and what a finding on
# it does. ⛔ `BLOCKS` is only for a check whose finding is a fact about the
# text; a check read at a density reports, because a density is a proxy for the
# rule rather than the rule. The keys are asserted against the surface below, in
# both directions.
HELD = {
    "Opening": [("the opening is the finding", BLOCKS, check_opening_is_the_finding)],
    "Length": [("shortening is by selection", BLOCKS, check_no_compression)],
    "Emphasis": [("emphasis is not the texture", REPORTS, check_emphasis_is_not_the_texture)],
    "Register": [("the register is reference", REPORTS, check_register_is_reference)],
    "Uncertainty": [("uncertainty is stated once", REPORTS, check_uncertainty_is_stated_once)],
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


def already_blocked(turn: str) -> tuple[bool, str]:
    """Has this turn been handed back once already? And if unknown, why.

    The guard is per turn and not per session: a reply restated once has had its
    chance, and a hook that blocks the restatement too would hold the session
    open on a judgement the forbidding checks cannot make. ⚠️ The identifier is
    the harness's own turn id, and a payload without one falls back to the
    session, which blocks once per session rather than once per turn — the
    conservative direction.

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
        block = False
    else:
        handed_back, unguarded = already_blocked(turn)
        block = bool(blocking) and not handed_back

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
        said = f"Reply register: {len(blocking) + len(reported)} finding(s) against {CITATION}."
        if blocking and unguarded:
            said += f" Nothing was handed back: {unguarded}."
        out["systemMessage"] = said
    return out


def context(blocking: list[str], reported: list[str], block: bool, unguarded: str = "") -> str:
    lines = [f"The reply's register is procedure: {CITATION}. Findings against the reply just sent:"]
    lines += [f"- {f}" for f in blocking + reported]
    if block:
        lines.append(
            "Restate the reply so each holds. This turn is handed back once only; a second "
            "reply is not blocked, so get it right here."
        )
    elif blocking and unguarded:
        lines.append(
            f"Nothing is blocked, and not because these findings are weak: {unguarded}. "
            "Restate the reply anyway."
        )
    else:
        lines.append(
            "Nothing is blocked: these findings are read at a density, or this turn has had "
            "its one hand-back. The next reply is written knowing them."
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
    ("the register is reference", "an inequality and an image, which are not exclamations",
     "The guard compares a != b and c != d.\n\n![one](a.png) ![two](b.png) ![three](c.png)\n"),
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
    """A planted reply whose finding is of the given kind.

    ⚠️ Chosen by kind rather than by position in `REDDENS`. The first draft
    indexed the list, so inserting a plant silently repointed the assertions
    about what blocks and what reports to whichever plants had moved into those
    slots.
    """
    for name, _, reply in REDDENS:
        if any(k == kind for tests in HELD.values() for n, k, _ in tests if n == name):
            return reply
    raise AssertionError(f"no planted reply produces a {kind} finding")


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
    again = answer({"last_assistant_message": blocking_reply, "prompt_id": "self-test-block"})
    if "decision" not in again and again.get("systemMessage"):
        print("  ok                     the same turn is handed back once only")
    else:
        print("  FAIL                   the same turn was blocked twice")
        failures += 1
    unguardable = answer({"last_assistant_message": blocking_reply})
    if "decision" not in unguardable and "Nothing was handed back" in unguardable.get(
        "systemMessage", ""
    ):
        print("  ok                     a payload naming no turn reports, and says it could not guard")
    else:
        print("  FAIL                   a payload naming no turn did not say the guard was absent")
        failures += 1
    reported = answer({"last_assistant_message": reporting_reply, "prompt_id": "self-test-report"})
    if "decision" not in reported and reported.get("systemMessage"):
        print("  ok                     a reported finding blocks nothing")
    else:
        print("  FAIL                   a reported finding blocked")
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
