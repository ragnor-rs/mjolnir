#!/usr/bin/env python3
"""The two readings a duplicate search is judged between, and the reply that carries both.

⛔ **The rule is the filing role's** -- `../skills/file-work-item/SKILL.md`, in its duplicate
section -- and this module states none of it. What is here is what that role should not do by eye:

  * **A reading** -- the backlog listed with no keyword through the port's `search_items` (§ 3),
    reduced to its count, its highest identifier and the identifiers themselves.
  * **The comparison** -- an earlier reading against one taken now, naming what appeared.
  * **The reply held** -- that a reply carries both readings, the second later than the first, or
    says the window went unmeasured.

⚠️ **The whole set is compared and not the count and the highest alone.** One item created while
another is removed leaves the count standing, and a tracker whose identifiers are opaque has no
highest at all; the pair is what a reply states, being what a reader can check at a glance.

Usage:
    file_window.py read --out FILE        take a reading, keep it in FILE, print its line
    file_window.py compare --first FILE --out FILE
                                          take the reading before the write and compare the two
    file_window.py check --reply FILE     whether a reply carries both readings
    file_window.py --self-test

Exit status: 0 read, unmoved or held; 1 the backlog moved, or the reply does not hold; 2 the
configuration, a file or the tracker could not be read; 3 the window is unmeasured, this tracker
having no search. ⛔ 2 and 3 are not one answer: a search that failed is not an absent capability.
"""

from __future__ import annotations

import argparse
import datetime
import io
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface
import port  # noqa: E402 -- the one door to a tracker

UNMOVED, MOVED, UNREADABLE, UNMEASURED = 0, 1, 2, 3

# The bound on one listing. ⛔ Carried rather than left to an implementation's default, which is
# short enough that an ordinary backlog fills it and the count then stands still for ever.
LIMIT = 1000

FIRST, BEFORE_THE_WRITE = "first", "before the write"
NOT_MEASURED = "Backlog window: unmeasured"

LINE = re.compile(
    r"Backlog reading, (?P<which>first|before the write): (?P<count>\d+) items"
    r"(?: \(at the bound\))?, highest (?P<highest>\S+), at (?P<at>[0-9T:.+-]+Z?)"
)


class Stop(Exception):
    """A stop this module names, rather than a traceback a caller reads."""


def identifier(item: dict) -> str:
    """What names one item, in whichever shape its implementation answered with.

    ⛔ An item with no identifier is a stop: dropped, it is an item whose arrival no comparison
    can see.
    """
    for held in (item.get("number"), item.get("key"), item.get("id"),
                 (item.get("card") or {}).get("id"), item.get("url")):
        if held not in (None, ""):
            return str(held)
    raise Stop(f"an item of the listing carries no identifier -- {item.get('title')!r}")


def highest(identifiers: list[str]) -> str | None:
    """The highest identifier, or None where they are opaque and have no order."""
    numbered = []
    for one in identifiers:
        found = re.fullmatch(r"(?:[A-Za-z][A-Za-z0-9_]*-)?(\d+)", one)
        if found:
            numbered.append((int(found.group(1)), one))
    return max(numbered)[1] if numbered else None


def _now() -> str:
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def read(tracker) -> dict | None:
    """One reading of the backlog, or None where this tracker cannot be searched."""
    outcome = tracker.invoke("search_items", limit=LIMIT)
    if outcome.failed:
        raise Stop(f"the backlog could not be read -- {outcome.detail}")
    if not outcome.performed:
        return None
    answer = outcome.result or {}
    items = sorted({identifier(one) for one in answer.get("items") or []})
    return {
        "at": _now(),
        "count": len(items),
        "highest": highest(items),
        "at_limit": bool(answer.get("at_limit")),
        "items": items,
    }


def line(which: str, reading: dict) -> str:
    """One reading as the reply carries it."""
    bound = " (at the bound)" if reading["at_limit"] else ""
    return (f"Backlog reading, {which}: {reading['count']} items{bound}, "
            f"highest {reading['highest'] or 'none'}, at {reading['at']}")


def compare(first: dict, now: dict) -> dict:
    """What changed between two readings."""
    before, after = set(first["items"]), set(now["items"])
    return {
        "moved": before != after,
        "appeared": sorted(after - before),
        "gone": sorted(before - after),
        "lines": [line(FIRST, first), line(BEFORE_THE_WRITE, now)],
    }


def holds(reply: str) -> tuple[bool, str]:
    """Whether a reply carries both readings, and why not where it does not.

    ⛔ **The second has to be later than the first**, or one reading written out twice passes as
    two. ⚠️ A reply over several items carries a pair per item, so the two are read as pairs in
    the order they stand rather than as the presence of one of each.
    """
    found = [(one["which"], datetime.datetime.fromisoformat(one["at"].replace("Z", "+00:00")))
             for one in LINE.finditer(reply)]
    if NOT_MEASURED in reply:
        if found:
            return False, "the reply says the window is unmeasured and carries a reading"
        return True, "the window is stated unmeasured"
    if not found:
        return False, "the reply carries neither reading"
    if len(found) % 2:
        return False, "a reading stands without its pair"
    for opening, closing in zip(found[::2], found[1::2]):
        if (opening[0], closing[0]) != (FIRST, BEFORE_THE_WRITE):
            return False, "the readings are not a first and one before the write, in that order"
        if closing[1] <= opening[1]:
            return False, "the reading before the write is no later than the first"
    return True, "both readings are carried"


def _load(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as handle:
            held = json.load(handle)
    except (OSError, ValueError) as exc:
        raise Stop(f"{path}: the reading could not be read -- {exc}") from exc
    if not isinstance(held, dict) or not {"at", "count", "highest", "at_limit", "items"} <= set(held):
        raise Stop(f"{path}: is not a reading this module wrote")
    return held


def run(args, tracker) -> int:
    """`read` and `compare`, over whichever tracker they were handed."""
    first = _load(args.first) if args.what == "compare" else None
    now = read(tracker)
    if now is None:
        print(NOT_MEASURED)
        return UNMEASURED
    with open(args.out, "w", encoding="utf-8") as handle:
        json.dump(now, handle)
    if first is None:
        print(line(FIRST, now))
        return UNMOVED
    answer = compare(first, now)
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    return MOVED if answer["moved"] else UNMOVED


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="what")
    for name in ("read", "compare"):
        one = sub.add_parser(name)
        one.add_argument("--skills-root", default=".")
        one.add_argument("--out", required=True, help="where the reading taken now is kept")
        if name == "compare":
            one.add_argument("--first", required=True, help="the reading it is judged against")
    checking = sub.add_parser("check")
    checking.add_argument("--reply", required=True)
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    try:
        if args.what == "check":
            with open(args.reply, encoding="utf-8") as handle:
                held, why = holds(handle.read())
            print(why)
            return UNMOVED if held else MOVED
        if args.what is None:
            parser.error("one of read, compare and check is needed")
        return run(args, port.load(args.skills_root))
    except (Stop, config.ConfigError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return UNREADABLE


# --- the suite -------------------------------------------------------------

def self_test() -> int:
    from contextlib import redirect_stdout

    failures = 0

    def check(label: str, condition: bool, detail: object = "") -> None:
        nonlocal failures
        print(f"  {'ok  ' if condition else 'FAIL'}  {label}"
              + ("" if condition else f": {detail}"))
        failures += not condition

    configuration = None
    for name in sorted(os.listdir(config.EXAMPLES)):
        if name.endswith((".yaml", ".yml")):
            with open(os.path.join(config.EXAMPLES, name), encoding="utf-8") as handle:
                configuration = config.load_text(handle.read(), config.EXAMPLES)
            break
    assert configuration is not None, "no shipped example to hold a port over"

    asked: list[int] = []

    def tracker(items=None, *, failing=False, at_limit=False):
        def search(terms=None, *, labels=None, limit=100):
            asked.append(limit)
            if failing:
                raise port.HostUnavailable("planted")
            return {"items": items, "at_limit": at_limit, "limit": limit}
        return port.Port(configuration, port.port_spec(), adapter=port.Adapter(
            {} if items is None and not failing else {"search_items": search}))

    def stopped(call) -> bool:
        try:
            call()
        except Stop:
            return True
        return False

    print("The two readings:")
    one = read(tracker([{"number": 9}, {"number": 10}]))
    check("a reading carries the count and the highest, compared as numbers",
          (one["count"], one["highest"]) == (2, "10"), one)
    check("the bound is this module's own", asked == [LIMIT], asked)
    keyed = read(tracker([{"key": "AB-9"}, {"key": "AB-10"}]))
    check("a keyed identifier is ordered by its number", keyed["highest"] == "AB-10", keyed)
    opaque = read(tracker([{"number": None, "card": {"id": "x9"}}]))
    check("an opaque identifier is counted and has no highest",
          (opaque["count"], opaque["highest"], opaque["items"]) == (1, None, ["x9"]), opaque)
    check("an item with no identifier is a stop",
          stopped(lambda: read(tracker([{"title": "unnamed"}]))))
    check("a search that failed is a stop and never an unmeasured window",
          stopped(lambda: read(tracker(failing=True))))
    check("an absent search is no reading", read(tracker()) is None)
    check("a listing at its bound says so",
          "(at the bound)" in line(FIRST, read(tracker([{"number": 1}], at_limit=True))))

    print("The comparison:")
    same = compare(one, read(tracker([{"number": 10}, {"number": 9}])))
    check("the same backlog is unmoved", not same["moved"], same)
    swapped = compare(one, read(tracker([{"number": 10}, {"number": 8}])))
    check("a swap under one count and one highest is still a move",
          (swapped["moved"], swapped["appeared"], swapped["gone"]) == (True, ["8"], ["9"]), swapped)

    print("The reply:")
    later = read(tracker([{"number": 9}, {"number": 10}, {"number": 11}]))
    opening, closing = compare(one, later)["lines"]
    for label, reply, expected in (
        ("both readings hold", f"- {opening}\n- {closing}\n", True),
        ("a pair per item holds", "\n".join([opening, closing] * 2), True),
        ("an opaque tracker's pair holds",
         f"{line(FIRST, opaque)}\n{line(BEFORE_THE_WRITE, read(tracker([])))}", True),
        ("a bounded pair holds", "\n".join(
            line(w, dict(r, at_limit=True))
            for w, r in ((FIRST, one), (BEFORE_THE_WRITE, later))), True),
        ("a reply with no reading does not", "Nothing found.", False),
        ("the first reading alone does not", opening, False),
        ("the second reading alone does not", closing, False),
        ("the pair reversed does not", f"{closing}\n{opening}", False),
        ("one reading written twice does not",
         f"{opening}\n{line(BEFORE_THE_WRITE, one)}", False),
        ("a second item left with its first reading does not",
         f"{opening}\n{closing}\n{opening}", False),
        ("an unmeasured window, said, holds", NOT_MEASURED, True),
        ("an unmeasured window beside a reading does not", f"{NOT_MEASURED}\n{opening}", False),
    ):
        held, why = holds(reply)
        check(label, held is expected, why)

    print("The command line:")
    with tempfile.TemporaryDirectory() as directory:
        first, now, reply = (os.path.join(directory, n) for n in ("first", "now", "reply"))

        def ran(what, subject):
            args = argparse.Namespace(what=what, first=first, out=first if what == "read" else now)
            printed = io.StringIO()
            with redirect_stdout(printed):
                return run(args, subject), printed.getvalue()

        check("an unsearchable tracker exits unmeasured and keeps no reading",
              ran("read", tracker()) == (UNMEASURED, NOT_MEASURED + "\n")
              and not os.path.exists(first))
        check("a reading is taken and kept", ran("read", tracker([{"number": 1}]))[0] == UNMOVED)
        check("an unmoved backlog exits zero",
              ran("compare", tracker([{"number": 1}]))[0] == UNMOVED)
        status, printed = ran("compare", tracker([{"number": 1}, {"number": 2}]))
        check("a moved one does not, and names what appeared",
              status == MOVED and json.loads(printed)["appeared"] == ["2"], printed)
        with open(reply, "w", encoding="utf-8") as handle:
            handle.write("\n".join(json.loads(printed)["lines"]))
        with redirect_stdout(io.StringIO()):
            answered = main(["check", "--reply", reply])
        check("the lines a comparison prints are the lines a reply is held to",
              answered == UNMOVED)
        with open(first, "w", encoding="utf-8") as handle:
            handle.write("{}")
        check("a file that is no reading is a stop", stopped(lambda: _load(first)))

    print("The role:")
    with open(os.path.join(HERE, "..", "skills", "file-work-item", "SKILL.md"),
              encoding="utf-8") as handle:
        role = handle.read()
    for what in ("read", "compare", "check"):
        check(f"the filing role runs `{what}`",
              f'/scripts/{os.path.basename(__file__)}" {what} ' in role)
    check("the filing role names the unmeasured statement", NOT_MEASURED in role)

    print(f"\n{'FAILED' if failures else 'OK'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
