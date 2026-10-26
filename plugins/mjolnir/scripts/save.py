#!/usr/bin/env python3
"""The bookkeeping role's two derivations: which thirds run, and the artifact's form.

`session.parts` (§ 23) and the save artifact are one role's facts with more than
one reader -- the role writes an artifact and a later pass reads one -- so the
derivation lives here rather than in the role's own text. ⛔ **That is § 10's
rule for a branch name, one role over**: a form copied into a role's text is a
form allowed to disagree with the thing that holds a written artifact to it, and
the direction nothing reports is the reader accepting an artifact that is missing
what a resume needs.

⛔ **It states no rule of its own.** Which thirds there are, the order they run
in, when a save is owed and what the artifact is for are `../config/schema.md`
§ 23's, read through the shared reader. What this module owns is what neither of
its readers should perform twice:

  * **The thirds this project runs**, in the procedure's order rather than the
    order a configuration happens to list them in, each with what it reads and
    whether that mechanism is there at all.
  * **The form** of a save artifact: the fields a resuming pass needs, and the
    boundary vocabulary.
  * **The reading back** of a written artifact against that form -- which is both
    how the writing role checks what it wrote and how a resuming pass reads it,
    the same answer serving both because they are the same question asked from
    two sides.

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
    save.py [--skills-root DIR]        the thirds this project runs, in order
    save.py form [--skills-root DIR]   the fields a save artifact carries
    save.py check --file PATH          hold a written artifact to the form, and
                                       report what a resuming pass reads out of it

Exit status, and ⛔ **four values rather than two**: 0 the artifact holds or the
report was produced, 1 the artifact does not hold, 2 the configuration could not
be read, 3 there is nothing to answer about -- this project maps no bookkeeping
role, or states no configuration at all. ⚠️ The last is § 11's rule at a command
line: *no answer* collapsed into 0 reads as an artifact that passed, and into 1
as a role whose every save is wrong.
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
        "a store of its own, which no key on this surface declares yet (#35)"
    ),
    "commit": "this role's own `commit.staging` entry (§ 6)",
}

# The one third whose mechanism the surface does not carry, named here because
# the reader reports the same absence and the two have to agree. ⛔ A third
# listed here is reported unavailable rather than skipped: a third that silently
# did not run reads exactly like one that did.
WITHOUT_A_MECHANISM = {"memory"}


def _place(stated: list) -> list[dict]:
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
            "available": name not in WITHOUT_A_MECHANISM,
            "placed": name in ORDER,
        }
        for name in placed + unplaced
    ]


def thirds(configuration: config.Config) -> list[dict]:
    """Which thirds run here, in the procedure's order, each with its state."""
    return _place(list(configuration.get("session.parts") or []))


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

# ⛔ The boundaries § 23 states, as the field's closed set. A save taken at a
# boundary this does not name is an artifact whose reader cannot tell what it is
# holding, so the value is refused rather than passed through.
BOUNDARIES = ["handoff", "compaction", "session_end", "asked"]


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


def read(text: str) -> tuple[dict | None, list[str]]:
    """(the fields a resuming pass reads, the problems holding it to the form).

    ⛔ Parsed through the one reader's YAML rather than a grammar of its own: an
    artifact is a configuration-shaped file, and a second parser for one format
    is the defect this module is an instance of refusing.
    """
    try:
        document = config._load_yaml(text, "the save artifact")
    except config.ConfigError as exc:
        return None, [str(exc)]
    if not isinstance(document, dict):
        return None, [
            f"the artifact is {type(document).__name__} rather than a block of "
            "fields, so none of the form's fields can be read out of it"
        ]

    problems = []
    known = {name for name, _ in FIELDS}
    for name, carries in FIELDS:
        if name not in document:
            problems.append(f"`{name}` is missing, and it carries {carries}")
            continue
        value = document[name]
        if value is None or (isinstance(value, str) and not value.strip()):
            problems.append(
                f"`{name}` is written and empty, which reads as answered and is "
                f"not: it carries {carries}"
            )
    for name in sorted(set(document) - known):
        problems.append(
            f"`{name}` is not a field of the form, so whatever it carries is read "
            "by nothing. The form is this module's and not the writing role's"
        )
    boundary = document.get("boundary")
    if boundary is not None and boundary not in BOUNDARIES:
        problems.append(
            f"`boundary` is {boundary!r}; § 23 states {' | '.join(BOUNDARIES)}. A "
            "boundary a reader cannot place is a save it cannot tell mid-item from "
            "finished"
        )
    recovered = {name: document.get(name) for name, _ in FIELDS}
    return recovered, problems


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


# (label, how to write it, a fragment the refusal has to name)
PLANTED = [
    ("a field left out", lambda: _without("acceptance"), "`acceptance` is missing"),
    ("the boundary left out", lambda: _without("boundary"), "`boundary` is missing"),
    ("a field written empty", lambda: _an_artifact(committed='""'), "`committed` is written and empty"),
    ("a boundary outside its set", lambda: _an_artifact(boundary="whenever"), "`boundary` is 'whenever'"),
    ("a field the form does not carry", lambda: _an_artifact(mood="hopeful"),
     "`mood` is not a field of the form"),
    ("an artifact that is not a block of fields", lambda: "- just a list\n",
     "rather than a block of fields"),
    ("an artifact that does not parse", lambda: "boundary: [unclosed\n", "the save artifact"),
]


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
    # ⛔ Stated as an equivalence rather than as *memory is unavailable*, so the
    # arm keeps holding the day that third acquires a store.
    check(
        "a third with no mechanism is reported unavailable rather than dropped",
        all(
            entry["available"] == (entry["part"] not in WITHOUT_A_MECHANISM)
            for entry in thirds(live)
        ),
        f"came back {thirds(live)!r}",
    )
    check(
        "the order this module places and the surface's vocabulary agree",
        set(ORDER) == set(live.facts.get("enums", {}).get("session.parts", [])),
        "a third the surface states is placed nowhere here, or the other way "
        "round -- either leaves a third running in an order nothing decided",
    )
    check(
        "every third this module places names what it reads",
        set(ORDER) <= set(READS),
        f"placed {ORDER!r} and names {sorted(READS)!r}",
    )
    check(
        "and the third with no mechanism is one the surface states",
        WITHOUT_A_MECHANISM <= set(ORDER),
        f"{WITHOUT_A_MECHANISM!r} against {ORDER!r}",
    )
    # ⛔ The reader reports the same absence, and nothing but this holds the two
    # statements to each other: a third this module calls unavailable while the
    # reader reports it carried is a role told to skip a third that can run, and
    # the other direction is a role running one that cannot.
    stated_here = set(live.get("session.parts") or [])
    check(
        "this project states a third with no mechanism, so that arm was asked",
        bool(WITHOUT_A_MECHANISM & stated_here),
        f"{WITHOUT_A_MECHANISM!r} against {sorted(stated_here)!r} -- with no "
        "overlap the agreement below is asserted over nothing",
    )
    for third in sorted(WITHOUT_A_MECHANISM & stated_here):
        check(
            f"the reader reports `{third}` unavailable too",
            any(
                third in line and "unavailable" in line
                for line in live.unavailable()
            ),
            f"reported {live.unavailable()!r}",
        )

    print()
    print("a project that maps no bookkeeping role, and one that states nothing")
    import tempfile  # noqa: PLC0415 -- the only arm that needs a directory

    with tempfile.TemporaryDirectory() as root:
        check(
            "a project stating no configuration is told so rather than refused",
            main(["--skills-root", root]) == NOTHING_TO_ANSWER,
            "whoever invoked this by name is owed the answer that the project "
            "states nothing, which § 7 makes an invitation rather than silence",
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

    shape = sub.add_parser("form", help="the fields a save artifact carries")
    shape.add_argument("--skills-root", default=".")

    reading = sub.add_parser("check", help="hold a written artifact to the form")
    reading.add_argument("--skills-root", default=".")
    reading.add_argument("--file", required=True)

    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    # ⛔ The form is this module's and is answered before any configuration is
    # read: it is procedure, so a project that configures nothing still has one.
    if args.what == "form":
        print(json.dumps(form(), indent=2, ensure_ascii=False))
        return 0

    if args.what == "check":
        try:
            with open(args.file, encoding="utf-8") as handle:
                text = handle.read()
        except OSError as exc:
            print(exc, file=sys.stderr)
            return 2
        recovered, problems = read(text)
        print(json.dumps(
            {"holds": not problems, "problems": problems, "read": recovered},
            indent=2, ensure_ascii=False,
        ))
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
    if not running:
        report.append(
            "No bookkeeping role runs here (`session.parts: []`), so there is no "
            "third to run and nothing to save (§ 23)."
        )
    print(json.dumps(
        {"parts": running, "store": configuration.get("context.artifacts.carrier"),
         "report": report},
        indent=2, ensure_ascii=False,
    ))
    return 0 if running else NOTHING_TO_ANSWER


if __name__ == "__main__":
    sys.exit(main())
