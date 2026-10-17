#!/usr/bin/env python3
"""Hold a role's reply to the register the surface fixes for it.

The surface makes language, register and audience configurable per artifact and
fixes one of them: the reply a role writes in the session, whose audience the
project does not choose. That rule is procedure -- see the surface's § 8, *The
reply to the person running a role* -- and this is what holds a reply to it
instead of the writer's judgement at the time of writing.

It runs as a `Stop` hook, which is the only place the finished reply exists: the
harness hands the hook `last_assistant_message`, so nothing here parses a
transcript or guesses at what was sent. Two properties are held by *forbidding*
checks, whose forms are stable, and a finding there blocks the stop once and
hands the reply back for restating. Three more are *computed* from thresholds,
which are proxies rather than rules, so a finding there is reported and nothing
is blocked. One property is held by nothing, and that is written down here and
in `docs/single-source-of-truth.md` rather than left to read as coverage.

The property list is read out of the surface at run time. A row added to that
table therefore reddens `--self-test` until somebody either holds it or states
why it is not held -- the same direction as the gate's orphan-section check, one
surface over. Thresholds and patterns are grammar and live here.

Usage:
    check_reply_register.py              read a hook payload on stdin, answer on stdout
    check_reply_register.py --self-test  assert every check reddens on each of its
                                         planted violations, then hold the surface's
                                         property list to being wholly accounted for
"""

from __future__ import annotations

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

FORBIDDING, COMPUTED = "forbidding", "computed"

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

# Shortening by compression: a line that has stopped being sentences. One arrow
# is a mapping and is legitimate -- `open → closed` says something a sentence
# would say worse -- so the form forbidden is the *chain*.
ARROW = re.compile(r"→|⇒|->|=>")
ARROWS_PER_LINE_ALLOWED = 1

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
EXCLAMATION = re.compile(r"!")
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

FENCE = re.compile(r"^\s*```")
CODE_SPAN = re.compile(r"`[^`\n]*`")
TABLE_ROW = re.compile(r"^\s*\|")
HEADING = re.compile(r"^\s*#{1,6}\s+")
QUOTE = re.compile(r"^\s*>")


# --- reading the reply -----------------------------------------------------


def prose(reply: str, *, tables: bool = False) -> list[str]:
    """The lines of a reply that are prose, in order.

    Fenced blocks go whole, inline code spans are removed from the lines that
    survive, and a table row is prose only where a check asks for it: a cell is
    where this repository's own documents put a mapping arrow and a bolded term,
    so sweeping rows would redden on the shape the register asks for.
    """
    out, fenced = [], False
    for line in reply.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced or not line.strip():
            continue
        if TABLE_ROW.match(line) and not tables:
            continue
        out.append(CODE_SPAN.sub(" ", line))
    return out


def opening(reply: str) -> str:
    """The first line that carries the reply's own words."""
    for line in prose(reply, tables=True):
        if HEADING.match(line) or QUOTE.match(line):
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
        if len(ARROW.findall(line)) > ARROWS_PER_LINE_ALLOWED:
            findings.append(
                f"Length: a line is compressed into an arrow chain — {line.strip()[:60]!r}. "
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
    body = "\n".join(prose(reply))
    hits = len(DRAMATIC.findall(body)) + len(EXCLAMATION.findall(body))
    if hits > DRAMATIC_ALLOWED:
        return [
            f"Register: {hits} dramatic words or exclamations read as narrative rather than as "
            f"a textbook stating a result (over {DRAMATIC_ALLOWED})."
        ]
    return []


def check_uncertainty_is_stated_once(reply: str) -> list[str]:
    body = "\n".join(prose(reply))
    hits = len(HEDGE.findall(body))
    if hits > HEDGES_ALLOWED:
        return [
            f"Uncertainty: {hits} hedges read as hedging throughout rather than as uncertainty "
            f"stated plainly and once (over {HEDGES_ALLOWED})."
        ]
    return []


# Which property of the surface's table each check holds, and of which kind. A
# forbidding check blocks; a computed one reports. ⛔ The keys are asserted
# against the surface below, in both directions.
HELD = {
    "Opening": [("the opening is the finding", FORBIDDING, check_opening_is_the_finding)],
    "Length": [("shortening is by selection", FORBIDDING, check_no_compression)],
    "Emphasis": [("emphasis is not the texture", COMPUTED, check_emphasis_is_not_the_texture)],
    "Register": [("the register is reference", COMPUTED, check_register_is_reference)],
    "Uncertainty": [("uncertainty is stated once", COMPUTED, check_uncertainty_is_stated_once)],
}

# What is held by nothing, with the reason it is not held. Stated here as well as
# in the document, because this is the file somebody edits when they add a check
# and the residue has to be in front of them when they do.
RESIDUE = {
    "Structure": (
        "whether continuous prose was carrying enumerable facts is a judgement about the "
        "facts, not about the text: the same paragraph is correct prose or a table withheld "
        "depending on what it says. A reader covers it."
    ),
    "Length": (
        "the padding half. Whether a sentence earns its place cannot be computed, and a "
        "length threshold would punish the content that needs the room — which is the rule's "
        "own first clause. Only the compression half is held."
    ),
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
    return problems


# --- the answer the harness reads ------------------------------------------


def findings(reply: str) -> tuple[list[str], list[str]]:
    """(blocking, reported) findings against one reply."""
    blocking, reported = [], []
    for tests in HELD.values():
        for _, kind, test in tests:
            (blocking if kind == FORBIDDING else reported).extend(test(reply))
    return blocking, reported


def already_blocked(turn: str) -> bool:
    """Has this turn been handed back once already?

    The guard is per turn and not per session: a reply restated once has had its
    chance, and a hook that blocks the restatement too would hold the session
    open on a judgement the forbidding checks cannot make. ⚠️ The identifier is
    the harness's own turn id, and a payload without one falls back to the
    session, which blocks once per session rather than once per turn — the
    conservative direction.
    """
    root = os.environ.get("CLAUDE_PLUGIN_DATA") or tempfile.gettempdir()
    seen = Path(root) / "reply-register-turns"
    try:
        seen.mkdir(parents=True, exist_ok=True)
        marker = seen / re.sub(r"[^A-Za-z0-9_-]", "-", turn)[:120]
        if marker.exists():
            return True
        marker.touch()
        files = sorted(seen.iterdir(), key=lambda p: p.stat().st_mtime)
        for stale in files[:-500]:
            stale.unlink(missing_ok=True)
        return False
    except OSError:
        # No state, so no guard: report rather than block, which cannot loop.
        return True


def answer(payload: dict) -> dict:
    reply = payload.get("last_assistant_message") or ""
    if not reply.strip():
        return {}
    blocking, reported = findings(reply)
    if not blocking and not reported:
        return {}

    turn = str(payload.get("prompt_id") or payload.get("session_id") or "")
    block = bool(blocking) and bool(turn) and not already_blocked(turn)
    out: dict = {
        "hookSpecificOutput": {
            "hookEventName": "Stop",
            "additionalContext": context(blocking, reported, block),
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
            f"Reply register: {len(blocking) + len(reported)} finding(s) against {CITATION}."
        )
    return out


def context(blocking: list[str], reported: list[str], block: bool) -> str:
    lines = [f"The reply's register is procedure: {CITATION}. Findings against the reply just sent:"]
    lines += [f"- {f}" for f in blocking + reported]
    if block:
        lines.append(
            "Restate the reply so each holds. This turn is handed back once only; a second "
            "reply is not blocked, so get it right here."
        )
    else:
        lines.append(
            "Nothing is blocked: these are threshold checks, or this turn has had its one "
            "hand-back. The next reply is written knowing them."
        )
    return "\n".join(lines)


def hook(stream) -> int:
    """Answer one payload. ⛔ Fails open, and says so.

    A hook that crashes on every turn is worse than one that holds nothing, and
    a hook that holds nothing while reporting green is worse than both. So an
    internal failure answers with a message naming itself rather than with
    silence or with a non-zero exit.
    """
    try:
        payload = json.load(stream)
        out = answer(payload if isinstance(payload, dict) else {})
    except Exception as error:  # noqa: BLE001 — any failure here must stay non-fatal
        print(json.dumps({
            "systemMessage": (
                f"Reply register: the check did not run ({type(error).__name__}), so this "
                "reply was held to nothing."
            )
        }))
        return 0
    if out:
        print(json.dumps(out))
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
]

SURFACE_PLANTS = [
    ("a property with no check and no stated reason",
     lambda text: text.replace(
         "| Emphasis | Where a fact is load-bearing | As a default texture |",
         "| Emphasis | Where a fact is load-bearing | As a default texture |\n"
         "| Cadence | Sentences that vary in length | A single rhythm |",
     )),
    ("a renamed property, leaving a check with nothing behind it",
     lambda text: text.replace("| Emphasis | Where a fact", "| Stress | Where a fact")),
    ("a subsection whose heading no longer slugs to the anchor",
     lambda text: text.replace(
         "### The reply to the person running a role",
         "### The reply to whoever is running a role",
     )),
]


def self_test() -> int:
    by_name = {
        name: test
        for tests in HELD.values()
        for name, _, test in tests
    }
    failures = 0
    uncovered = [name for name in by_name if not any(n == name for n, _, _ in REDDENS)]
    for name in uncovered:
        print(f"  NO PLANTED VIOLATION   {name}")
        failures += 1

    print(f"Asserting each check reddens on its planted violations ({len(REDDENS)}):")
    for name, label, reply in REDDENS:
        if by_name[name](reply):
            print(f"  red on                 {name}: {label}")
        else:
            print(f"  STAYED GREEN           {name}: {label}")
            failures += 1

    print(f"\nAsserting each stays green where it must ({len(STAY_GREEN)}):")
    for name, label, reply in STAY_GREEN:
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

    # ⚠️ The turn guard is state on disk, so these four assertions run against a
    # directory of their own. Without it the second run of this self-test reads
    # the first run's markers and reports that a forbidding finding does not
    # block — measured, and exactly the shape of a check that passes once.
    os.environ["CLAUDE_PLUGIN_DATA"] = tempfile.mkdtemp(prefix="reply-register-self-test-")

    print("\nAsserting the answer the harness reads:")
    blocked = answer({
        "last_assistant_message": REDDENS[0][2],
        "prompt_id": "self-test-block",
    })
    if blocked.get("decision") == "block" and "additionalContext" in blocked.get(
        "hookSpecificOutput", {}
    ):
        print("  ok                     a forbidding finding blocks the stop and is handed back")
    else:
        print("  FAIL                   a forbidding finding did not block")
        failures += 1
    again = answer({
        "last_assistant_message": REDDENS[0][2],
        "prompt_id": "self-test-block",
    })
    if "decision" not in again and again.get("systemMessage"):
        print("  ok                     the same turn is handed back once only")
    else:
        print("  FAIL                   the same turn was blocked twice")
        failures += 1
    computed = answer({
        "last_assistant_message": REDDENS[6][2],
        "prompt_id": "self-test-report",
    })
    if "decision" not in computed and computed.get("systemMessage"):
        print("  ok                     a computed finding reports and blocks nothing")
    else:
        print("  FAIL                   a computed finding blocked")
        failures += 1
    if answer({"last_assistant_message": CLEAN, "prompt_id": "self-test-clean"}) == {}:
        print("  ok                     a reply in register produces no answer at all")
    else:
        print("  FAIL                   a reply in register produced an answer")
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
    problems = check_every_property_is_accounted_for(SURFACE.read_text(encoding="utf-8"))
    print()
    print(f"  {'FAIL' if problems else 'ok  '}  every property of the register is accounted for")
    if problems:
        print(f"\n{len(problems)} problem(s):\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1
    held = sum(len(t) for t in HELD.values())
    print(
        f"\nThe register's properties are read from the surface and wholly accounted for: "
        f"{held} held, {len(RESIDUE)} stated as unheld."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
