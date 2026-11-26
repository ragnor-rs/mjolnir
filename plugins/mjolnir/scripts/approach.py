#!/usr/bin/env python3
"""Hold the person's go on an item's approach before the implementing leg's first edit.

The rule is `plugins/mjolnir/config/schema.md § 43`, which states it and the
argument behind it. Neither is restated here.

⛔ **This module never decides the approach and never answers the ask.** What
it holds is the part a carrier can: whether the project asks at all, whether an
ask carries the reading and the plan the person is to see, whether a record of
the answer names somebody other than the route that asked, and what the record
on the item says when the leg comes to its first edit. Only an approved record,
read back from the item, lets the leg write.

Usage:
    approach.py decide                       whether this project asks (exit 3 where not)
    approach.py form                         the ask's format and fields
    approach.py check --file F               read an ask, refuse a shape § 43 refuses
    approach.py record --item N --answer A --given G --by B
                                             write the answer onto the item as a comment
    approach.py read --item N                read the answer back off the item
    approach.py --self-test                  plant each refused shape and assert the refusal

Exit status: 0 the answer was produced (for `read`: an approved record), 1 the
ask or the record was refused, or `read` found no approved record, 2 the
configuration, the file or the tracker could not be read, 3 the project does not
ask.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config as reader  # noqa: E402 -- the one reader, never a second parser

KEY = "approach_ask"
ASKED_PATH = f"{KEY}.asked"
NEVER, BEFORE_FIRST_EDIT = "never", "before_first_edit"
APPROVED, DECLINED = "approved", "declined"
ANSWERS = (APPROVED, DECLINED)
NONE_RECORDED, UNREAD = "none", "unread"
CITATION = "§ 43"

# The ask's form. ⛔ Each field's meaning is § 43's; what is written here is only
# the spelling a role writes and this module reads.
FORM = {
    "item": "the item asked about, by identifier",
    "reading": "the item as this role read it: its outcome, in this role's words",
    "condition": "acceptance | outcome -- what the bullets below were read off (§ 4.4)",
    "bullets": "the condition, one string per bullet, as the item states it",
    "plan": "the intended change, one string per step: what is written, and where",
}

# The comment a record is written as. The first line is what `read` keys on, so
# a comment anybody writes about the ask in prose is never read as an answer.
MARKER = "<!-- mjolnir:approach-ask -->"
ANSWER_LINE = re.compile(r"^- answer: (?P<answer>\S+)\s*$", re.MULTILINE)
BY_LINE = re.compile(r"^- by: (?P<by>.+?)\s*$", re.MULTILINE)

# ⛔ Words that name the route rather than a person. A record answered by any of
# them is the route approving its own approach, which § 43 refuses: the go is
# the person's, and a pass that cannot reach one stops instead.
ROUTE_WORDS = ("role", "claude", "agent", "assistant", "model", "self", "automatic",
               "autonomous", "unattended", "implement", "procedure")


class AskError(Exception):
    """An ask or a record § 43 refuses, named so the role can fix it."""


# --- whether the project asks -----------------------------------------------


def decide(resolved) -> dict:
    """Whether the implementing leg asks before its first edit."""
    asked = resolved.get(ASKED_PATH) or NEVER
    runs = asked == BEFORE_FIRST_EDIT
    return {
        "asked": asked,
        "runs": runs,
        "reason": (
            f"`{ASKED_PATH}: {BEFORE_FIRST_EDIT}`, so the implementing leg puts the reading and "
            "the plan to the person and makes no edit until `read` finds an approved record on "
            f"the item. A run that cannot reach a person stops here and approves nothing ({CITATION})."
            if runs
            else f"`{ASKED_PATH}` is `{asked}`, so the implementing leg asks nothing before its "
            f"first edit and its reply mentions no ask ({CITATION})."
        ),
    }


# --- the ask ----------------------------------------------------------------


def _strings(value, where: str) -> list:
    if not isinstance(value, list) or not value:
        raise AskError(f"the ask's `{where}` is empty; it is a list of one string or more ({CITATION}).")
    for index, entry in enumerate(value):
        if not isinstance(entry, str) or not entry.strip():
            raise AskError(
                f"entry {index + 1} of the ask's `{where}` is not a non-empty string ({CITATION})."
            )
    return value


def check(ask, resolved) -> dict:
    """Refuse a shape § 43 refuses; otherwise the ask as it is to be put."""
    if not decide(resolved)["runs"]:
        raise AskError(
            f"this project does not ask (`{ASKED_PATH}` is not `{BEFORE_FIRST_EDIT}`); an ask "
            f"nobody configured is not put to anybody ({CITATION})."
        )
    if not isinstance(ask, dict):
        raise AskError(f"the ask is not a mapping of the form's fields ({CITATION}).")
    if set(ask) & {"answer", "approved", "given", "by"}:
        raise AskError(
            "the ask carries its own answer; the ask is the question, and the answer is the "
            f"person's, written by `record` once they give it ({CITATION})."
        )
    extra = set(ask) - set(FORM)
    if extra:
        raise AskError(f"the ask carries {sorted(extra)}, which the form does not ({CITATION}).")
    missing = [field for field in FORM if field not in ask]
    if missing:
        raise AskError(f"the ask does not carry {missing} ({CITATION}).")
    item = ask["item"]
    if isinstance(item, bool) or not isinstance(item, (str, int)) or not str(item).strip():
        raise AskError(f"the ask names no item ({item!r}); it is the item's identifier ({CITATION}).")
    if not isinstance(ask["reading"], str) or not ask["reading"].strip():
        raise AskError(
            f"the ask states no reading; the person is shown the item as this role read it ({CITATION})."
        )
    if ask["condition"] not in ("acceptance", "outcome"):
        raise AskError(
            f"the condition {ask['condition']!r} is neither `acceptance` nor `outcome` ({CITATION})."
        )
    bullets = _strings(ask["bullets"], "bullets")
    if ask["condition"] == "outcome" and len(bullets) != 1:
        raise AskError(
            "the ask reads an item's outcome as several bullets; an item stating no acceptance "
            f"condition is read as one ({CITATION})."
        )
    plan = _strings(ask["plan"], "plan")
    return {
        "holds": True,
        "item": str(item),
        "reading": ask["reading"],
        "condition": ask["condition"],
        "bullets": bullets,
        "plan": plan,
        "asks": "one question: approve this approach, or decline it",
    }


# --- the record -------------------------------------------------------------


def names_the_route(by: str) -> str | None:
    """The word in `by` that names the route rather than a person, if any."""
    words = re.findall(r"[a-z]+", by.lower())
    for word in words:
        for route in ROUTE_WORDS:
            if word == route or (len(route) > 4 and word.startswith(route)):
                return word
    return None


def record_body(answer: str, given: str, by: str, at: str) -> str:
    """The comment a record is written as."""
    return "\n".join([
        MARKER,
        f"**The approach was put to a person before the first edit** (schema {CITATION}).",
        "",
        f"- answer: {answer}",
        f"- given: {json.dumps(given, ensure_ascii=False)}",
        f"- by: {by}",
        f"- at: {at}",
    ])


def record(port, item: str, answer: str, given: str, by: str, at: str | None = None) -> dict:
    """Write the answer onto the item, refusing a record the route gave itself."""
    if answer not in ANSWERS:
        raise AskError(f"the answer {answer!r} is not one of {' | '.join(ANSWERS)} ({CITATION}).")
    if not given.strip() or not by.strip():
        raise AskError(
            "a record states the answer as it came back and who gave it, and one of the two "
            f"is empty ({CITATION}). Nothing was written."
        )
    route = names_the_route(by)
    if route:
        raise AskError(
            f"the answer is recorded as given by {by!r}, and `{route}` names the route rather "
            "than a person. ⛔ Nothing was written: the go on the approach is the person's, and "
            f"a run that cannot reach one stops rather than approving itself ({CITATION})."
        )
    when = at or datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    outcome = port.invoke("comment", item, record_body(answer, given, by, when))
    if not outcome.performed:
        return {"recorded": False, "detail": outcome.detail, "failed": bool(outcome.failed)}
    return {"recorded": True, "item": str(item), "answer": answer, "by": by, "at": when}


def read(port, item: str) -> dict:
    """What the item says about the ask: the latest record, and whether it lets the leg write."""
    outcome = port.invoke("read_comments", item)
    if not outcome.performed:
        return {
            "answer": UNREAD,
            "writes": False,
            "detail": (
                f"the item's comments could not be read ({outcome.detail}). ⛔ An unread record "
                f"is not an approval, so the leg makes no edit ({CITATION})."
            ),
        }
    comments = (outcome.result or {}).get("comments") or []
    latest = None
    for entry in comments:
        body = entry.get("body") or ""
        if body.startswith(MARKER):
            latest = entry
    if latest is None:
        return {
            "answer": NONE_RECORDED,
            "writes": False,
            "detail": f"no answer to the ask is recorded on item {item}, so the leg makes no edit ({CITATION}).",
        }
    if latest.get("edited"):
        return {
            "answer": UNREAD,
            "writes": False,
            "detail": (
                "the latest record was edited after it was written, so what it says is not the "
                f"answer as it was given. ⛔ It is not read as an approval ({CITATION})."
            ),
        }
    body = latest.get("body") or ""
    found = ANSWER_LINE.search(body)
    answer = found.group("answer") if found else None
    by = BY_LINE.search(body)
    if answer not in ANSWERS:
        return {
            "answer": UNREAD,
            "writes": False,
            "detail": f"the latest record states no answer this carrier reads ({CITATION}).",
        }
    return {
        "answer": answer,
        "writes": answer == APPROVED,
        "by": by.group("by") if by else None,
        "at": latest.get("created"),
        "detail": (
            f"approved on item {item}, so the leg may write ({CITATION})."
            if answer == APPROVED
            else f"declined on item {item}: the pass ends with the claim and the tree kept, and "
            f"nothing is written ({CITATION})."
        ),
    }


# --- the command ------------------------------------------------------------


def form() -> dict:
    """What `form` prints: the file's format first, since `check` reads nothing else."""
    return {
        "format": "one JSON object carrying exactly these fields",
        "fields": FORM,
        "answers": list(ANSWERS),
    }


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skills-root", default=".")
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("decide")
    sub.add_parser("form")
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--file", required=True)
    record_parser = sub.add_parser("record")
    record_parser.add_argument("--item", required=True)
    record_parser.add_argument("--answer", required=True, choices=ANSWERS)
    record_parser.add_argument("--given", required=True, help="the answer, as it came back")
    record_parser.add_argument("--by", required=True, help="the person who gave it")
    record_parser.add_argument("--at", default=None, help="when; now where omitted")
    read_parser = sub.add_parser("read")
    read_parser.add_argument("--item", required=True)
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.command == "form":
        print(json.dumps(form(), indent=2, ensure_ascii=False))
        return 0
    if args.command not in ("decide", "check", "record", "read"):
        parser.print_usage(sys.stderr)
        return 2
    try:
        resolved = reader.load(args.skills_root)
    except reader.ConfigError as error:
        print(str(error), file=sys.stderr)
        return 2
    decided = decide(resolved)
    if args.command == "decide":
        print(json.dumps(decided, indent=2, ensure_ascii=False))
        return 0 if decided["runs"] else 3
    if not decided["runs"]:
        print(json.dumps(decided, indent=2, ensure_ascii=False))
        return 3
    try:
        if args.command == "check":
            try:
                with open(args.file, encoding="utf-8") as handle:
                    ask = json.load(handle)
            except (OSError, ValueError) as error:
                print(f"the ask could not be read: {error}", file=sys.stderr)
                return 2
            answer = check(ask, resolved)
        else:
            import port as ports  # noqa: PLC0415 -- only the two tracker arms need it

            tracker = ports.load(args.skills_root)
            if args.command == "record":
                answer = record(tracker, args.item, args.answer, args.given, args.by, args.at)
                print(json.dumps(answer, indent=2, ensure_ascii=False))
                return 0 if answer["recorded"] else 2
            answer = read(tracker, args.item)
            print(json.dumps(answer, indent=2, ensure_ascii=False))
            if answer["answer"] == UNREAD and "could not be read" in answer["detail"]:
                return 2
            return 0 if answer["writes"] else 1
    except AskError as error:
        print(json.dumps({"holds": False, "refused": str(error)}, indent=2, ensure_ascii=False))
        return 1
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    return 0


# --- the suite --------------------------------------------------------------


def _resolved(block: str | None):
    """The none example, with § 43's block replaced by `block` where one is given."""
    example = os.path.join(HERE, "..", "config", "examples", "none.yaml")
    with open(example, encoding="utf-8") as handle:
        text = handle.read()
    text = re.sub(rf"(?m)^{KEY}:\n(?:  .*\n)*", "", text)
    if block is not None:
        text += "\n" + block
    return reader.load_text(text, os.path.dirname(example), check_paths=False)


class _Outcome:
    def __init__(self, performed, result=None, detail="", failed=False):
        self.performed, self.result, self.detail, self.failed = performed, result, detail, failed


class _FakeTracker:
    """A tracker holding one item's comments in memory, for the two tracker arms."""

    def __init__(self, readable=True, writable=True):
        self.comments: list = []
        self.readable, self.writable = readable, writable

    def invoke(self, operation, *args):
        if operation == "comment":
            if not self.writable:
                return _Outcome(False, detail="the tracker writes no comment")
            self.comments.append({"body": args[1], "created": "2026-11-27T00:00:00Z",
                                  "edited": None, "author": "someone"})
            return _Outcome(True, {"commented": True})
        if operation == "read_comments":
            if not self.readable:
                return _Outcome(False, detail="the call did not go through", failed=True)
            return _Outcome(True, {"number": args[0], "comments": list(self.comments)})
        raise AssertionError(operation)


def self_test() -> int:
    failures = 0

    def check_that(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}" + ("" if ok else f": {detail}"))
        if not ok:
            failures += 1

    def refused(call, fragment: str) -> tuple[bool, str]:
        try:
            answer = call()
        except AskError as error:
            return fragment in str(error), str(error)
        return False, f"held: {answer}"

    unstated = _resolved(None)
    never = _resolved(f"{KEY}:\n  asked: {NEVER}\n")
    asks = _resolved(f"{KEY}:\n  asked: {BEFORE_FIRST_EDIT}\n")

    print("Whether the project asks:")
    check_that("an unstated block asks nothing", decide(unstated)["runs"] is False,
               f"{decide(unstated)}")
    check_that("`never` asks nothing", decide(never)["runs"] is False)
    check_that("`before_first_edit` asks", decide(asks)["runs"] is True)
    check_that("the asking reason names the stop for a run that cannot reach a person",
               "stops here and approves nothing" in decide(asks)["reason"])

    def ask(**over):
        base = {"item": "7", "reading": "the feature is missing from the export",
                "condition": "acceptance", "bullets": ["the export carries the feature"],
                "plan": ["add the field in src/export.py", "a case in tests/test_export.py"]}
        base.update(over)
        return base

    check_that("the form names the format `check` reads", "JSON" in form()["format"])

    print("\nThe ask, green and planted:")
    held = check(ask(), asks)
    check_that("an ask carrying a reading, the bullets and a plan holds",
               held["holds"] and held["plan"] == ask()["plan"], f"{held}")
    planted = [
        ("an ask where the project does not ask", lambda: check(ask(), unstated),
         "does not ask"),
        ("an ask carrying its own answer", lambda: check({**ask(), "answer": APPROVED}, asks),
         "carries its own answer"),
        ("an ask with no plan", lambda: check(ask(plan=[]), asks), "`plan` is empty"),
        ("an ask with a blank plan step", lambda: check(ask(plan=[" "]), asks),
         "not a non-empty string"),
        ("an ask with no reading", lambda: check(ask(reading=""), asks), "no reading"),
        ("an ask with no bullets", lambda: check(ask(bullets=[]), asks), "`bullets` is empty"),
        ("an outcome read as several bullets",
         lambda: check(ask(condition="outcome", bullets=["a", "b"]), asks), "read as one"),
        ("a condition outside the two", lambda: check(ask(condition="vibe"), asks),
         "neither"),
        ("an ask naming no item", lambda: check(ask(item=None), asks), "names no item"),
        ("a field outside the form", lambda: check({**ask(), "risk": "low"}, asks),
         "the form does not"),
    ]
    for name, call, fragment in planted:
        ok, said = refused(call, fragment)
        check_that(f"{name} is refused", ok, said)

    print("\nThe record, and what the leg reads back:")
    tracker = _FakeTracker()
    nothing = read(tracker, "7")
    check_that("⛔ no record lets the leg write nothing",
               nothing["answer"] == NONE_RECORDED and nothing["writes"] is False, f"{nothing}")
    for by in ("the implementing role", "Claude", "this agent", "an autonomous run",
               "self-approved"):
        ok, said = refused(lambda by=by: record(tracker, "7", APPROVED, "yes", by),
                           "names the route")
        check_that(f"⛔ a record given by {by!r} is refused as the route approving itself",
                   ok and tracker.comments == [], said)
    ok, said = refused(lambda: record(tracker, "7", APPROVED, " ", "the person"), "is empty")
    check_that("a record with no words given is refused", ok, said)
    ok, said = refused(lambda: record(tracker, "7", "maybe", "hm", "the person"), "not one of")
    check_that("an answer outside the two is refused", ok, said)

    written = record(tracker, "7", DECLINED, "no, not that way",
                     "the person running this session, through the approach ask")
    check_that("a person's decline is written onto the item", written["recorded"], f"{written}")
    declined = read(tracker, "7")
    check_that("⛔ a declined record lets the leg write nothing, and keeps the tree",
               declined["answer"] == DECLINED and declined["writes"] is False
               and "tree kept" in declined["detail"], f"{declined}")
    record(tracker, "7", APPROVED, "yes, go", "the person running this session")
    approved = read(tracker, "7")
    check_that("the latest record governs: an approval after a decline lets the leg write",
               approved["answer"] == APPROVED and approved["writes"] is True, f"{approved}")
    tracker.comments.append({"body": "On reflection, no.\n- answer: declined",
                             "created": "x", "edited": None})
    after_prose = read(tracker, "7")
    check_that("a prose comment carrying no marker is never read as a record",
               after_prose["answer"] == APPROVED
               and after_prose["by"] == "the person running this session", f"{after_prose}")
    tracker.comments[1]["edited"] = "2026-11-27T01:00:00Z"
    edited = read(tracker, "7")
    check_that("⛔ a record edited after it was written is not read as an approval",
               edited["answer"] == UNREAD and edited["writes"] is False, f"{edited}")
    # ⛔ A record has to survive the tracker's own document conversion: Jira
    # writes a comment as a document and reads it back as text, and a marker or
    # an answer line lost on the way reads as no record at all.
    from adapters import jira  # noqa: PLC0415 -- the one tracker that converts a body

    body = record_body(APPROVED, "yes", "the person", "2026-11-27T00:00:00Z")
    round_trip = jira.as_text(jira.as_document(body))
    converted = _FakeTracker()
    converted.comments.append({"body": round_trip, "created": "x", "edited": None})
    check_that("a record read back through Jira's document conversion still reads approved",
               read(converted, "7")["writes"] is True, f"{round_trip!r}")
    unreadable = read(_FakeTracker(readable=False), "7")
    check_that("⛔ comments that could not be read are not an approval",
               unreadable["answer"] == UNREAD and unreadable["writes"] is False, f"{unreadable}")
    unwritable = record(_FakeTracker(writable=False), "7", APPROVED, "yes", "the person")
    check_that("a tracker that writes no comment records nothing, and says so",
               unwritable["recorded"] is False, f"{unwritable}")

    with tempfile.TemporaryDirectory() as scratch:
        path = os.path.join(scratch, "ask.json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(ask(), handle)
        with open(path, encoding="utf-8") as handle:
            check_that("an ask written as JSON reads back whole",
                       check(json.load(handle), asks)["item"] == "7")

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
