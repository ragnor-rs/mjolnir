#!/usr/bin/env python3
"""Put the rules nothing mechanical reads into the session, before anything is written.

Two of the surface's rules are held by being known rather than by a check --
`schema.md § 8 -> The reply to the person running a role` states that of the
register, and `§ 10 -> What a session standing in a tree can run` states it of
the shell a pinned session runs commands in. A rule enforced by being known has
to actually be known, so this is what makes it so: a `SessionStart` hook that
reads each subsection's own table out of the surface and hands it to the session
as context.

⛔ **No table is copied here, and neither are its column headings.** A second
statement of a rule in this file would be the defect the repository exists to
delete, and it would drift the first time somebody edited a row. What is written
here is where to find each table, one sentence of framing per rule, and how to
render it.

⚠️ **Why this event and not the one that holds the reply afterwards.** Measured
2026-10-20, each with a random token no session could otherwise know: a `Stop`
answer's `systemMessage` never enters the writer's request, so a register
reported after the fact changed no text at all; a `SessionStart` answer's
`additionalContext` is named back exactly by the session it opens. The channel
that reaches the writer before the writing is the only one that can carry a
rule, and this is it.

⚠️ **Both rules are handed to every session of a project that states a
configuration, including the ones they are not live for yet.** A session is in
no tree when it opens and may enter one later,
and this event fires once -- so a rule scoped to the tree has to arrive before
the tree exists or not at all. ⛔ The alternative is not a later injection: a
session that enters a tree fires no event this hook can answer.

⛔ **Fails open, and silently.** A session is not the place to report that a
document could not be parsed: the cost of saying nothing is a session that
writes to its own judgement, which is what every session before this one did,
while the cost of failing loudly is a hook that interrupts a person's work over
a file they may be mid-edit on. ⚠️ What covers the silence is the gate: this
script's own run asserts every table is found and every row of each reaches the
context.

⛔ **And where the project states no configuration, the one message the surface
permits an unconfigured project is written here** -- `schema.md § 7 -> A hook in
a project that states no configuration`, which states that the invitation is the
whole of what such a project gets and that every other carrier is silent in it.
This is the carrier for that message because it answers the event the exception
is scoped to, and for no other reason: the rules below are not loaded there, a
project that configures nothing having adopted no procedure to be held to.

Usage:
    load_the_rules.py              read a hook payload on stdin, answer on stdout
    load_the_rules.py --self-test  assert each table is read out of the surface, that
                                   every row reaches the context, that an unconfigured
                                   project is invited and handed no rule, and that the
                                   carrier registers this script on the event that opens
                                   a session
"""

from __future__ import annotations

import io
import json
import re
import sys
import tempfile
from pathlib import Path

# --- where the rules live --------------------------------------------------

SURFACE = Path(__file__).resolve().parent.parent / "config" / "schema.md"

# The subsections whose tables this reads, by the anchors the code host would
# give their headings. Grammar: a heading may be reworded without touching this
# script only if its anchor survives, which is the bargain every citation of the
# surface already makes.
#
# ⛔ `lead` and `coda` are the only prose here, and each says what the table
# cannot say about itself -- that it is procedure, and which of its rows is held
# by something other than the reader. Neither restates a row.
RULES = [
    {
        "anchor": "the-reply-to-the-person-running-a-role",
        "citation": "schema § 8 → The reply to the person running a role",
        "lead": (
            "The register every reply you write in this session is held to ({citation}). "
            "It is procedure: no project configures it, and no check reads it — it holds "
            "because you have read it."
        ),
        "coda": (
            "Separately from the table above, and not part of any row of it: one of those "
            "properties is also held by a check, because it is an act rather than a property "
            "of prose. A reply that names work the turn does not do hands the turn back, and "
            "what the hand-back asks for is the work — under the current branch, pull request "
            "and item — or the one question that blocks it. It never asks for the reply to be "
            "rewritten."
        ),
    },
    {
        "anchor": "what-a-session-standing-in-a-tree-can-run",
        "citation": "schema § 10 → What a session standing in a tree can run",
        "lead": (
            "What a shell command may be once this session is standing in its own tree "
            "({citation}). It is procedure: the pinning is the harness's and no project "
            "configures it, and the table is what was measured rather than a grammar the "
            "harness publishes."
        ),
        "coda": (
            "This rule is live only while the session is standing in a tree, and it is handed "
            "to you now because entering one fires nothing that could hand it to you then. "
            "Until the session is in a tree, this table holds nothing."
        ),
    },
]

CITATION_PATTERN = "{citation}"

# The carrier that calls this script, and the event it registers for. ⛔ Held
# rather than assumed: a carrier naming a script that is not this one, or an
# event that does not open a session, leaves the gate green and the rules
# unloaded in every session -- which is indistinguishable from them not
# existing.
CARRIER = Path(__file__).resolve().parent.parent / "hooks" / "hooks.json"
CARRIER_EVENT = "SessionStart"

# The anchor of the subsection that states both of this script's answers -- the
# invitation and the silence around it. Grammar, as above: a reword is free, a
# reanchoring is not.
UNCONFIGURED_ANCHOR = "a-hook-in-a-project-that-states-no-configuration"

FENCE = re.compile(r"^\s{0,3}(?P<marker>`{3,}|~{3,})")
HEADING = re.compile(r"^\s*#{1,6}\s+")
TABLE_ROW = re.compile(r"^\s*\|")


# --- reading the surface ---------------------------------------------------


def anchor_of(heading_line: str) -> str:
    """The anchor the code host would give this heading."""
    title = re.sub(r"^\s*#{1,6}\s+", "", heading_line).strip().lower().replace("`", "")
    return re.sub(r"[^\w\s-]", "", title).replace(" ", "-")


def read_table(text: str, anchor: str) -> tuple[list[str], list[list[str]]]:
    """One subsection's table out of the surface, as (heading cells, rows).

    ⛔ **The heading row is read rather than carried.** A column name written
    into this file would be a second statement of the surface's own wording, and
    the rule this script exists to serve is that there is only ever one.

    Found by the anchor of the subsection it sits in rather than by its heading
    text or its position, for the reason the gate's own rulings table is found by
    a column header: a renumbering must not be a change this script has to be
    edited for. Reading stops at the next heading of any level, so a table added
    below the subsection is not parsed as a continuation of this one.
    """
    found, fenced = False, False
    header: list[str] = []
    rows: list[list[str]] = []
    for line in text.splitlines():
        if FENCE.match(line):
            fenced = not fenced
            continue
        if fenced:
            continue
        if HEADING.match(line):
            if found:
                break
            found = anchor_of(line) == anchor
            continue
        if not found or not TABLE_ROW.match(line):
            continue
        # ⚠️ Two, not three. The one table this read when it served a single
        # rule had three columns, and a count written against it would make a
        # two-column rule silently absent rather than refused -- which is the
        # failure this script's whole docstring is about.
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        head = re.sub(r"[*`]", "", cells[0])
        if not head or set(head) <= set("-: "):
            continue
        if not header:
            header = cells
            continue
        rows.append(cells)
    return (header, rows) if header and rows else ([], [])


def rendered(rule: dict, header: list[str], rows: list[list[str]]) -> str:
    """The context one rule is handed to the session as.

    ⚠️ The rows as the surface words them, and one sentence of framing. A
    paraphrase here would be a second statement of the rule with nothing holding
    it to the first, which is the whole reason each table is read rather than
    written.

    ⛔ **A table rather than a list of sentences, because the cells have to be
    delimited.** Measured on the first live run of this hook: rendered as
    `- Property — required. Not: forbidden`, a session read the last row's
    *forbidden* cell as running into the paragraph that followed it and quoted
    the splice back as the rule. A row's cells and a note about the table are
    different things, and prose alone did not keep them apart.
    """
    lines = [
        rule["lead"].replace(CITATION_PATTERN, rule["citation"]),
        "",
        "| " + " | ".join(header) + " |",
        "|" + "---|" * len(header),
    ]
    for cells in rows:
        lines.append("| " + " | ".join(cells) + " |")
    lines += ["", rule["coda"]]
    return "\n".join(lines)


def context(text: str) -> str:
    """Every rule that could be read, in the order they are stated above."""
    blocks = []
    for rule in RULES:
        header, rows = read_table(text, rule["anchor"])
        if rows:
            blocks.append(rendered(rule, header, rows))
    return "\n\n---\n\n".join(blocks)


def shared_reader():
    """The configuration reader beside this script, or None where it is gone.

    ⛔ Whether a project states a configuration is asked through it rather than
    by testing a path here: where that file lives is one statement, and the
    invitation below has to name the same path the reader resolves or it invites
    somebody to write a file nothing will read.
    """
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    try:
        import config  # noqa: PLC0415 -- the path is set one line up
        return config
    except Exception:  # noqa: BLE001 -- a session must not be interrupted by this
        return None


def invitation(reader) -> str:
    """The one message a project that states no configuration is given.

    ⛔ Every path in it comes from the reader or from this file's own location,
    so there is nothing here to go stale: the file to write is the path the
    reader resolves, and the keys are in the document it validates against.

    ⚠️ It goes to the person and never into the session's context. The channel
    that reaches a person is `systemMessage`, which the harness's own
    documentation of this event names for exactly this purpose, while
    `additionalContext` would hand the invitation to a session that cannot act
    on it and would then carry it into every reply it writes.
    """
    return (
        "mjolnir is installed and this project states no configuration, so nothing of it is "
        f"running here and nothing of it will interrupt you. To adopt it, write "
        f"`{reader.CONFIG_PATH}` under this directory: every key, its default and whether it "
        f"is required are stated in {SURFACE}, with an example configuration per shape in "
        f"{reader.EXAMPLES}."
    )


def answer(payload: dict) -> dict:
    reader = shared_reader()
    if reader is None:
        # ⛔ Silent, per the module docstring: an install whose own reader is
        # unreachable cannot tell whether this project adopted anything, and
        # neither of the two answers below is safe to give without knowing.
        return {}
    if not reader.configured(str(payload.get("cwd") or ".")):
        return {"systemMessage": invitation(reader)}
    loaded = context(SURFACE.read_text(encoding="utf-8"))
    if not loaded:
        return {}
    return {
        "hookSpecificOutput": {
            "hookEventName": CARRIER_EVENT,
            "additionalContext": loaded,
        }
    }


def check_the_carrier_still_calls_this(text: str) -> list[str]:
    """The carrier registers this script on the event that opens a session.

    ⛔ The same shape the sibling hook's check has, and for the same reason: a
    carrier that stopped naming this script would leave the rules unloaded
    with nothing saying so, and a session running to its own judgement looks
    exactly like a session that read them and ignored them.
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
# of a table would be a no-op the first time somebody reworded that row, and a
# no-op plant prints STAYED GREEN while asserting nothing.


def _plant_reworded_heading(text: str, anchor: str, rows: list[list[str]]) -> str:
    """Reword whichever heading carries this anchor, whatever its words are."""
    line = next(l for l in text.splitlines()
                if HEADING.match(l) and anchor_of(l) == anchor)
    return text.replace(line, "### A heading this script cannot find")


def _plant_no_rows_left(text: str, anchor: str, rows: list[list[str]]) -> str:
    """Drop every row of *that* table, leaving the heading row standing.

    ⚠️ Every row and not one of them: dropping a single row leaves a table that
    still parses, so the plant has to reach the condition the assertion is about
    — no row at all. Measured, as a plant that did not.
    """
    firsts = {re.sub(r"[*`]", "", cells[0]) for cells in rows}
    return "\n".join(
        line for line in text.splitlines()
        if not (TABLE_ROW.match(line)
                and re.sub(r"[*`]", "", line.strip().strip("|").split("|")[0].strip())
                in firsts))


def _plant_no_heading_row(text: str, anchor: str, rows: list[list[str]]) -> str:
    """Drop the table's heading row.

    ⛔ Not one of the plants above, because the consequence is not that nothing
    parses: the next row is read as the heading instead, which is exactly what
    makes it the plant that asserts the column names come from the document. A
    script carrying its own column names would render them over this unchanged.
    """
    header, _ = read_table(text, anchor)
    line = next(l for l in text.splitlines()
                if TABLE_ROW.match(l)
                and [c.strip() for c in l.strip().strip("|").split("|")] == header)
    return "\n".join(l for l in text.splitlines() if l != line)


SURFACE_PLANTS = [
    ("a subsection whose heading no longer slugs to the anchor", _plant_reworded_heading),
    ("a table under the anchor with no rows left", _plant_no_rows_left),
]

CARRIER_PLANTS = [
    ("a carrier that is not valid JSON", lambda text: text.rstrip()[:-1]),
    ("a carrier registering no handler for the event",
     lambda text: text.replace(f'"{CARRIER_EVENT}"', '"Notification"')),
    ("a carrier calling a script that is not this one",
     lambda text: text.replace("load_the_rules.py", "load_something_else.py")),
    ("a carrier whose expansion of the plugin root is mistyped",
     lambda text: text.replace("CLAUDE_PLUGIN_ROOT", "CLAUDE_PLUGIN_ROOTS")),
]


def self_test() -> int:
    failures = 0
    text = SURFACE.read_text(encoding="utf-8")
    loaded = context(text)

    for rule in RULES:
        anchor = rule["anchor"]
        header, rows = read_table(text, anchor)
        print(f"Asserting `{anchor}` is read out of the surface:")
        if not rows:
            print("  FAIL                   no row found; this rule would be absent")
            return 1
        print(f"  ok                     {len(rows)} row(s) under {len(header)} column(s)")

        # ⛔ Every row reaches the context, asserted row by row rather than by a
        # count: a renderer that dropped the last row would pass a count written
        # against itself.
        print("\nAsserting every row the surface carries reaches the session:")
        for cells in rows:
            first = cells[0]
            if first in loaded and cells[1][:40] in loaded:
                print(f"  ok                     {first[:72]}")
            else:
                print(f"  FAIL                   {first[:72]}: the row did not reach the context")
                failures += 1

        print("\nAsserting the column names are the surface's and not a copy:")
        # ⛔ The assertion is that they *move with the document*: with the
        # heading row gone, the next row is read as the heading. A script
        # carrying its own column names would answer the same either way.
        without = read_table(_plant_no_heading_row(text, anchor, rows), anchor)[0]
        if all(cell in loaded for cell in header) and without == rows[0]:
            print(f"  ok                     {' · '.join(header)}")
        else:
            print(f"  FAIL                   {header} does not come from the table's own "
                  f"heading row (without it: {without})")
            failures += 1

        print("\nAsserting the citation reaches the session with it:")
        if rule["citation"] in loaded:
            print(f"  ok                     {rule['citation']}")
        else:
            print(f"  FAIL                   {rule['citation']} is absent from the context")
            failures += 1

        print("\nAsserting a surface it cannot read loads nothing rather than guessing:")
        for label, plant in SURFACE_PLANTS:
            planted = plant(text, anchor, rows)
            if planted == text:
                print(f"  FAIL                   {label}: the plant was a no-op")
                failures += 1
                continue
            if not read_table(planted, anchor)[1]:
                print(f"  ok                     {label}")
            else:
                print(f"  FAIL                   {label}: still parsed a table")
                failures += 1
        print()

    # ⛔ The next rule's table is not this one's shape, and the reader must not
    # be written against the shapes that happen to be here now. Asserted over a
    # fabricated document rather than the surface, there being no two-column
    # rule to read yet.
    print("Asserting the reader is not written against three columns:")
    fabricated = ("### A rule with two columns\n\n| What | Instead |\n|---|---|\n"
                  "| a thing | another thing |\n")
    header, rows = read_table(fabricated, "a-rule-with-two-columns")
    if header == ["What", "Instead"] and rows == [["a thing", "another thing"]]:
        print("  ok                     a two-column table is read, heading row and all")
    else:
        print(f"  FAIL                   a two-column table read as {header} / {rows}")
        failures += 1
    single = "### A rule with one column\n\n| What |\n|---|\n| a thing |\n"
    if not read_table(single, "a-rule-with-one-column")[1]:
        print("  ok                     and a single-cell line is not a row of anything")
    else:
        print("  FAIL                   a single-cell line was read as a row")
        failures += 1
    print()

    # ⛔ One rule unreadable must not take the other down with it: the rules are
    # independent, and a session handed one of them is strictly better off than
    # a session handed none.
    print("Asserting one unreadable rule still leaves the others loaded:")
    for rule in RULES:
        others = [r["citation"] for r in RULES if r is not rule]
        planted = _plant_reworded_heading(text, rule["anchor"],
                                          read_table(text, rule["anchor"])[1])
        partial = context(planted)
        if rule["citation"] not in partial and all(c in partial for c in others):
            print(f"  ok                     without `{rule['anchor']}`")
        else:
            print(f"  FAIL                   dropping `{rule['anchor']}` did not leave "
                  f"{len(others)} rule(s) standing")
            failures += 1

    print("\nAsserting the surface still states what an unconfigured project gets:")
    anchors = {anchor_of(line) for line in text.splitlines() if HEADING.match(line)}
    if UNCONFIGURED_ANCHOR in anchors:
        print(f"  ok                     {UNCONFIGURED_ANCHOR}")
    else:
        print(f"  FAIL                   {UNCONFIGURED_ANCHOR} is not a heading of the surface, "
              "so the invitation below is this file's rule rather than the surface's")
        failures += 1
    reworded = _plant_reworded_heading(text, UNCONFIGURED_ANCHOR, [])
    if UNCONFIGURED_ANCHOR not in {anchor_of(line) for line in reworded.splitlines()
                                   if HEADING.match(line)}:
        print("  ok                     and reddens when that subsection is reanchored")
    else:
        print("  FAIL                   a reanchored subsection stayed green")
        failures += 1

    # ⛔ The two answers this hook has, each asserted against the other: an
    # invitation where nothing is stated, every rule where something is. A suite
    # holding one of them would pass a carrier that gave the same answer to both.
    # ⚠️ The planted project's file is written at the path the reader resolves
    # rather than at a literal, so a move of that path reddens here.
    print("\nAsserting a project that states no configuration is invited and handed no rule:")
    reader = shared_reader()
    with tempfile.TemporaryDirectory() as directory:
        bare = Path(directory) / "states-nothing"
        bare.mkdir()
        answered = answer({"cwd": str(bare)})
        message = str(answered.get("systemMessage", ""))
        if "hookSpecificOutput" not in answered:
            print("  ok                     no rule is handed to a session it holds nothing in")
        else:
            print(f"  FAIL                   context reached an unconfigured project: "
                  f"{str(answered)[:80]!r}")
            failures += 1
        if reader is not None and reader.CONFIG_PATH in message and str(SURFACE) in message:
            print("  ok                     and the invitation names the file to write and "
                  "where the keys are")
        else:
            print(f"  FAIL                   the invitation named neither: {message[:120]!r}")
            failures += 1

        adopted = Path(directory) / "states-one"
        stated = adopted / (reader.CONFIG_PATH if reader else "")
        stated.parent.mkdir(parents=True, exist_ok=True)
        stated.write_text("roots:\n  code: \".\"\n", encoding="utf-8")
        answered = answer({"cwd": str(adopted)})
        reached = str(answered.get("hookSpecificOutput", {}).get("additionalContext", ""))
        if reached == loaded and loaded:
            print("  ok                     and a project that states one is handed every rule")
        else:
            print(f"  FAIL                   a configured project was handed {reached[:80]!r}")
            failures += 1
        if "systemMessage" not in answered:
            print("  ok                     with nothing said to the person who configured it")
        else:
            print(f"  FAIL                   a configured project was invited to configure "
                  f"itself: {str(answered.get('systemMessage'))[:80]!r}")
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
        planted = plant(carrier)
        if planted == carrier:
            print(f"  FAIL                   {label}: the plant was a no-op")
            failures += 1
        elif check_the_carrier_still_calls_this(planted):
            print(f"  ok                     {label}")
        else:
            print(f"  FAIL                   {label}: stayed green")
            failures += 1

    print()
    if failures:
        print(f"{failures} assertion(s) failed.")
        return 1
    print(
        f"{len(RULES)} rule(s) are read from the surface and handed to every session of a "
        f"project that states a configuration: {len(loaded)} characters of context. A project "
        "that states none is invited to write one and handed nothing. Nothing here judges what "
        "a session then does."
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
