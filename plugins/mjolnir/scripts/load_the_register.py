#!/usr/bin/env python3
"""Put the register a role's reply is held to into the session, before anything is written.

The register is a rule and nothing mechanical reads it -- `schema.md § 8 -> The
reply to the person running a role` states that, and states why. A rule enforced
by being known has to actually be known, so this is what makes it so: a
`SessionStart` hook that reads the surface's own table and hands it to the
session as context.

⛔ **The table is read at run time and never copied here.** A second statement of
the register in this file would be the defect the repository exists to delete,
and it would drift the first time somebody edited a row. What is written here is
where to find the table and how to render it.

⚠️ **Why this event and not the one that holds the reply afterwards.** Measured
2026-10-20, each with a random token no session could otherwise know: a `Stop`
answer's `systemMessage` never enters the writer's request, so a register
reported after the fact changed no text at all; a `SessionStart` answer's
`additionalContext` is named back exactly by the session it opens. The channel
that reaches the writer before the writing is the only one that can carry a
rule, and this is it.

⛔ **Fails open, and silently.** A session is not the place to report that a
document could not be parsed: the cost of saying nothing is a session that
writes to its own judgement, which is what every session before this one did,
while the cost of failing loudly is a hook that interrupts a person's work over
a file they may be mid-edit on. ⚠️ What covers the silence is the gate: this
script's own run asserts the table is found and every row reaches the context.

Usage:
    load_the_register.py              read a hook payload on stdin, answer on stdout
    load_the_register.py --self-test  assert the table is read out of the surface, that
                                      every row reaches the context, and that the carrier
                                      registers this script on the event that opens a session
"""

from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

# --- where the rule lives --------------------------------------------------

SURFACE = Path(__file__).resolve().parent.parent / "config" / "schema.md"

# The subsection whose table this reads, by the anchor the code host would give
# its heading. Grammar: the heading may be reworded without touching this script
# only if its anchor survives, which is the bargain every citation of the
# surface already makes.
TABLE_ANCHOR = "the-reply-to-the-person-running-a-role"

CITATION = "schema § 8 → The reply to the person running a role"

# The carrier that calls this script, and the event it registers for. ⛔ Held
# rather than assumed: a carrier naming a script that is not this one, or an
# event that does not open a session, leaves the gate green and the register
# unloaded in every session -- which is indistinguishable from the rule not
# existing.
CARRIER = Path(__file__).resolve().parent.parent / "hooks" / "hooks.json"
CARRIER_EVENT = "SessionStart"

FENCE = re.compile(r"^\s{0,3}(?P<marker>`{3,}|~{3,})")
HEADING = re.compile(r"^\s*#{1,6}\s+")
TABLE_ROW = re.compile(r"^\s*\|")


# --- reading the surface ---------------------------------------------------


def read_register(text: str) -> list[tuple[str, str, str]]:
    """The register's table, as (property, required, not) rows, out of the surface.

    Found by the anchor of the subsection it sits in rather than by its heading
    text or its position, for the reason the gate's own rulings table is found by
    a column header: a renumbering must not be a change this script has to be
    edited for. Reading stops at the next heading of any level, so a table added
    below the subsection is not parsed as a continuation of this one.
    """
    found, fenced, rows = False, False, []
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if HEADING.match(line):
            if found:
                break
            title = re.sub(r"^\s*#{1,6}\s+", "", line).strip().lower().replace("`", "")
            found = re.sub(r"[^\w\s-]", "", title).replace(" ", "-") == TABLE_ANCHOR
            continue
        if not found or not TABLE_ROW.match(line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3:
            continue
        head = re.sub(r"[*`]", "", cells[0])
        if not head or set(head) <= set("-: ") or head == "Property":
            continue
        rows.append((head, cells[1], cells[2]))
    return rows


def rendered(rows: list[tuple[str, str, str]]) -> str:
    """The context a session is handed.

    ⚠️ The rows as the surface words them, and one sentence of framing. A
    paraphrase here would be a second statement of the rule with nothing holding
    it to the first, which is the whole reason the table is read rather than
    written.

    ⛔ **A table rather than a list of sentences, because the cells have to be
    delimited.** Measured on the first live run of this hook: rendered as
    `- Property — required. Not: forbidden`, a session read the last row's
    *forbidden* cell as running into the paragraph that followed it and quoted
    the splice back as the rule. A row's three cells and a note about the table
    are four different things, and prose alone did not keep them apart.
    """
    lines = [
        f"The register every reply you write in this session is held to ({CITATION}). "
        "It is procedure: no project configures it, and no check reads it — it holds because "
        "you have read it.",
        "",
        "| Property | Required | Not |",
        "|---|---|---|",
    ]
    for prop, required, forbidden in rows:
        lines.append(f"| {prop} | {required} | {forbidden} |")
    lines += [
        "",
        "Separately from the table above, and not part of any row of it: one of those properties "
        "is also held by a check, because it is an act rather than a property of prose. A reply "
        "that names work the turn does not do hands the turn back, and what the hand-back asks "
        "for is the work — under the current branch, pull request and item — or the one question "
        "that blocks it. It never asks for the reply to be rewritten.",
    ]
    return "\n".join(lines)


def answer(payload: dict) -> dict:
    text = SURFACE.read_text(encoding="utf-8")
    rows = read_register(text)
    if not rows:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": CARRIER_EVENT,
            "additionalContext": rendered(rows),
        }
    }


def check_the_carrier_still_calls_this(text: str) -> list[str]:
    """The carrier registers this script on the event that opens a session.

    ⛔ The same shape the sibling hook's check has, and for the same reason: a
    carrier that stopped naming this script would leave the register unloaded
    with nothing saying so, and a session running to its own judgement looks
    exactly like a session that read the rule and ignored it.
    """
    name = Path(__file__).name
    try:
        carrier = json.loads(text)
    except json.JSONDecodeError as error:
        return [f"the carrier is not valid JSON ({error.msg})"]
    handlers = (carrier.get("hooks") or {}).get(CARRIER_EVENT)
    if not handlers:
        return [f"the carrier registers no handler for `{CARRIER_EVENT}`"]
    called = json.dumps(handlers)
    problems = []
    if name not in called:
        problems.append(f"no `{CARRIER_EVENT}` handler calls `{name}`")
    if "${CLAUDE_PLUGIN_ROOT}" not in called:
        problems.append(
            f"a `{CARRIER_EVENT}` handler names this script by a path the plugin root does not "
            "expand — the handler must address it through `${CLAUDE_PLUGIN_ROOT}`"
        )
    return problems


def hook(stream, out=None) -> int:
    """Answer one payload. ⛔ Fails open and says nothing, per the module docstring."""
    out = out if out is not None else sys.stdout
    try:
        payload = json.load(stream)
        answered = answer(payload if isinstance(payload, dict) else {})
    except Exception:  # noqa: BLE001 — a session must not be interrupted by this
        return 0
    if answered:
        print(json.dumps(answered), file=out)
    return 0


# --- the plants ------------------------------------------------------------
#
# ⛔ A plant may not name the content it plants into: a plant spelling out a row
# of the table would be a no-op the first time somebody reworded that row, and a
# no-op plant prints STAYED GREEN while asserting nothing.

SURFACE_PLANTS = [
    ("a subsection whose heading no longer slugs to the anchor",
     lambda text, rows: text.replace(
         next(l for l in text.splitlines()
              if HEADING.match(l)
              and re.sub(r"[^\w\s-]", "",
                         re.sub(r"^\s*#{1,6}\s+", "", l).strip().lower().replace("`", "")
                         ).replace(" ", "-") == TABLE_ANCHOR),
         "### A heading this script cannot find")),
    # ⚠️ Every row of *that* table, not one of them: dropping a single row leaves
    # a table that still parses, so the plant has to reach the condition the
    # assertion is about — no row at all. Measured, as a plant that did not.
    ("a table under the anchor with no rows left",
     lambda text, rows: "\n".join(
         line for line in text.splitlines()
         if not (TABLE_ROW.match(line)
                 and any(re.sub(r"[*`]", "", line.strip().strip("|").split("|")[0].strip())
                         == prop for prop, _, _ in rows)))),
]

CARRIER_PLANTS = [
    ("a carrier that is not valid JSON", lambda text: text.rstrip()[:-1]),
    ("a carrier registering no handler for the event",
     lambda text: text.replace(f'"{CARRIER_EVENT}"', '"Notification"')),
    ("a carrier calling a script that is not this one",
     lambda text: text.replace("load_the_register.py", "load_something_else.py")),
    ("a carrier whose expansion of the plugin root is mistyped",
     lambda text: text.replace("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOTS")),
]


def self_test() -> int:
    failures = 0
    text = SURFACE.read_text(encoding="utf-8")
    rows = read_register(text)

    print("Asserting the register is read out of the surface:")
    if rows:
        print(f"  ok                     {len(rows)} row(s) found under the subsection's anchor")
    else:
        print("  FAIL                   no row found; the context would be empty")
        failures += 1
        return 1

    # ⛔ Every row reaches the context, asserted row by row rather than by a
    # count: a renderer that dropped the last row would pass a count written
    # against itself.
    context = rendered(rows)
    print("\nAsserting every row the surface carries reaches the session:")
    for prop, required, _ in rows:
        if prop in context and required[:40] in context:
            print(f"  ok                     {prop}")
        else:
            print(f"  FAIL                   {prop}: the row did not reach the context")
            failures += 1

    print("\nAsserting the context is the surface's wording and not a copy:")
    # The rendered context must contain no sentence about the register that the
    # surface does not carry — held as: every row's own cells come from `rows`,
    # which came from the surface. What is asserted here is the inverse risk, a
    # row this file invented.
    invented = [p for p, _, _ in rows if f"| {p} |" not in text and f"| {p}" not in text]
    if not invented:
        print("  ok                     every property named in the context is a row of the table")
    else:
        print(f"  FAIL                   properties not in the surface: {invented}")
        failures += 1

    print("\nAsserting a surface it cannot read loads nothing rather than guessing:")
    for label, plant in SURFACE_PLANTS:
        planted = plant(text, rows)
        if planted == text:
            print(f"  FAIL                   {label}: the plant was a no-op")
            failures += 1
            continue
        if not read_register(planted):
            print(f"  ok                     {label}")
        else:
            print(f"  FAIL                   {label}: still parsed a table")
            failures += 1

    print("\nAsserting the hook fails open and interrupts nothing:")
    out = io.StringIO()
    if hook(io.StringIO("not json at all"), out) == 0 and not out.getvalue():
        print("  ok                     a payload it cannot read is answered with silence")
    else:
        print(f"  FAIL                   a broken payload answered {out.getvalue()[:80]!r}")
        failures += 1

    print("\nAsserting the carrier still calls this script on the event that opens a session:")
    carrier = CARRIER.read_text(encoding="utf-8")
    problems = check_the_carrier_still_calls_this(carrier)
    if not problems:
        print("  ok                     the carrier as it stands registers this script")
    else:
        for problem in problems:
            print(f"  FAIL                   {problem}")
            failures += 1
    for label, plant in CARRIER_PLANTS:
        if check_the_carrier_still_calls_this(plant(carrier)):
            print(f"  ok                     {label}")
        else:
            print(f"  FAIL                   {label}: stayed green")
            failures += 1

    print()
    if failures:
        print(f"{failures} assertion(s) failed.")
        return 1
    print(
        f"The register is read from the surface and handed to every session: {len(rows)} rows, "
        f"{len(context)} characters of context. Nothing here judges a reply."
    )
    return 0


def main(argv: list[str]) -> int:
    unknown = [a for a in argv if a != "--self-test"]
    if unknown:
        print(f"unrecognised argument(s): {' '.join(unknown)}\n\n{__doc__}")
        return 2
    if "--self-test" not in argv:
        return hook(sys.stdin)
    return self_test()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
