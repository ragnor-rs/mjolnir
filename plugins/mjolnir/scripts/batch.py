#!/usr/bin/env python3
"""What a deploy's batch command is handed, and what its answer is matched against.

⛔ **The rule is § 33's** -- `../config/schema.md`, under *What the batch command is handed* -- and
this module states none of it. What is here is what the deploying role should not do by eye:

  * **The handed set** -- the backlog read through the port's `search_items` (§ 3), each item
    placed against `statuses` by the port, and the ones holding the roles a purpose hands kept.
  * **The run** -- the project's own command, resolved by the reader with the run's target,
    commit, grouping value and choices put in place, run once per purpose with the handed
    identifiers on its input.
  * **The match** -- what it printed against what it was handed, naming both differences.

⚠️ **Nothing here advances, holds or decides.** The carried set is a candidate list: the role
reads each item's role again where it advances it, and whether a precondition holds the target
is the role's reading of the answer rather than this module's verdict.

Usage:
    batch.py run --target NAME [--commit SHA] [--grouping-value VALUE] [--choose NAME=VALUE ...]
    batch.py --self-test

Exit status: 0 answered; 2 the configuration, the backlog or the command could not be read or
run; 3 the target carries no batch. ⛔ An answer naming nothing carried is 0 and not 3: a command
that found nothing and a target with no command are not one statement.
"""

from __future__ import annotations

import argparse
import io
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface
import port  # noqa: E402 -- the one door to a tracker

ANSWERED, UNREADABLE, NO_BATCH = 0, 2, 3

# The bound on the backlog read. ⛔ Carried rather than left to an implementation's default,
# which an ordinary backlog fills -- and a handed set cut by a bound reads as a complete one.
LIMIT = 1000

# How long a project's batch command may run. It reads and prints; a deploy is not waiting
# on a build here.
TIMEOUT = 300


class Stop(Exception):
    """A stop this module names, rather than a traceback a caller reads."""


def _key(word: str) -> str:
    """One identifier as two answers compare it: `#12` and `12` are one item."""
    return word.strip().lstrip("#").casefold()


def backlog(tracker) -> dict | None:
    """Every item the tracker holds, placed against `statuses`, or None where it cannot be read.

    ⛔ **None is the absent capability and never an empty backlog.** A search that failed is a
    stop; a tracker with no search takes § 33's fallback, which the answer names.
    """
    outcome = tracker.invoke("search_items", limit=LIMIT)
    if outcome.failed:
        raise Stop(f"the backlog could not be read -- {outcome.detail}")
    if not outcome.performed:
        return None
    answer = outcome.result or {}
    items = list(answer.get("items") or [])
    ladder = tracker.roles()
    # ⚠️ Any role places every item: what is read off the answer is each item's own
    # role, and the bar the first role sets is one nothing here reads.
    placed = tracker.short_of(ladder[0], items) if ladder and items else {}
    return {
        "at_limit": bool(answer.get("at_limit")),
        "placed": [
            {"item": str(one["item"]), "title": one.get("title"), "role": one["role"]}
            for one in placed.get("placed") or []
            if one.get("item") is not None
        ],
        "unplaced": [
            {"item": str(one.get("item")), "title": one.get("title"), "word": one.get("word")}
            for one in placed.get("unanswered") or []
        ],
    }


def handed_roles(tracker, resolved: dict, purpose: str) -> list[str]:
    """The roles § 33 hands the command for one purpose."""
    if purpose == config.ADVANCE:
        return tracker.roles_before(resolved["advances"])[-1:]
    if purpose == config.PRECONDITION:
        return tracker.roles_before(resolved["requires_role"])
    return []


def _ran(command: str, where: str, given: str) -> tuple[int, str, str]:
    """Run a project's own command in its root, whole, with the identifiers on its input."""
    done = subprocess.run(
        command, shell=True, cwd=where, input=given, capture_output=True, text=True,
        timeout=TIMEOUT,
    )
    return done.returncode, done.stdout, done.stderr


def answer(tracker, resolved: dict, read: dict | None, run=_ran) -> dict:
    """Every purpose run and matched, over a backlog already read."""
    out = {
        "target": resolved["target"],
        "commit": resolved["commit"],
        "choices": resolved["choices"],
        "backlog": (
            "unread: this tracker has no search, so the command is the batch's only source "
            "of candidates and nothing it left out can be named (§ 33)"
            if read is None
            else ("read, at its bound, so the handed set may be short" if read["at_limit"]
                  else "read whole")
        ),
        "purposes": [],
    }
    for one in resolved["purposes"]:
        purpose = one["purpose"]
        roles = handed_roles(tracker, resolved, purpose)
        handed = (
            None if read is None
            else [entry for entry in read["placed"] if entry["role"] in roles]
        )
        given = "".join(f"{entry['item']}\n" for entry in handed or [])
        if one.get("reachable") is False:
            raise Stop(f"the batch command's directory {one['runs_at']!r} is not there")
        try:
            status, printed, said = run(one["command"], one["runs_at"], given)
        except (OSError, subprocess.SubprocessError) as broken:
            raise Stop(f"the batch command could not be run for the {purpose}: {broken}") from None
        if status != 0:
            raise Stop(
                f"the batch command exited {status} for the {purpose}, so what it carries is "
                f"unread rather than nothing: {said.strip() or 'no stderr'}"
            )
        returned = list(dict.fromkeys(line.strip() for line in printed.splitlines() if line.strip()))
        got = {_key(word) for word in returned}
        row = {
            "purpose": purpose,
            "command": one["command"],
            "runs_at": one["runs_at"],
            "handed_roles": roles,
            "returned": returned,
        }
        if handed is None:
            row["carried"] = returned
            row["not_returned"] = None
            row["not_handed"] = None
        else:
            held = {_key(entry["item"]) for entry in handed}
            row["handed"] = [entry["item"] for entry in handed]
            row["carried"] = [word for word in returned if _key(word) in held]
            row["not_returned"] = [entry for entry in handed if _key(entry["item"]) not in got]
            row["not_handed"] = [word for word in returned if _key(word) not in held]
            row["unplaced_returned"] = [
                entry for entry in read["unplaced"] if _key(entry["item"]) in got
            ]
        out["purposes"].append(row)
    return out


def run(args, tracker, resolved_by=None, ran=_ran) -> int:
    """`run`, over whichever tracker and reader it was handed."""
    resolved = (resolved_by or config.load(args.skills_root)).deploy_batch(
        args.target, args.choose, args.commit, getattr(args, "grouping_value", None)
    )
    if resolved["batch"] is None:
        print(f"The target {args.target!r} carries no batch (§ 33), so nothing is handed "
              "and nothing is matched.")
        return NO_BATCH
    print(json.dumps(answer(tracker, resolved, backlog(tracker), ran), indent=2,
                     ensure_ascii=False))
    return ANSWERED


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="what")
    running = sub.add_parser("run")
    running.add_argument("--skills-root", default=".")
    running.add_argument("--target", required=True, help="the target's `name` (§ 33)")
    running.add_argument("--commit", help="the commit this deploy serves, as the run read it")
    running.add_argument("--choose", action="append", metavar="NAME=VALUE",
                         help="one of the run's choices, exactly as the go shows it")
    running.add_argument("--grouping-value", metavar="VALUE",
                         help="the grouping's own value the go names, for a command "
                         "placing {deploy:grouping}")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.what is None:
        parser.error("`run` is needed")
    try:
        return run(args, port.load(args.skills_root))
    except (Stop, config.ConfigError, OSError, ValueError) as exc:
        print(exc, file=sys.stderr)
        return UNREADABLE


# --- the suite -------------------------------------------------------------

def self_test() -> int:
    from contextlib import redirect_stdout

    import yaml

    failures = 0

    def check(label: str, condition: bool, detail: object = "") -> None:
        nonlocal failures
        print(f"  {'ok  ' if condition else 'FAIL'}  {label}"
              + ("" if condition else f": {detail}"))
        failures += not condition

    # ⛔ The one shipped example whose code root is the directory it sits in, so a command run
    # here runs somewhere real; its own ladder is what every role below is read off.
    with open(os.path.join(config.EXAMPLES, "github-projects.yaml"), encoding="utf-8") as handle:
        shipped = yaml.safe_load(handle)
    ladder = [status["role"] for status in shipped["statuses"]]
    words = {status["role"]: status["name"] for status in shipped["statuses"]}
    first, early, landed, last = ladder[0], ladder[1], ladder[-2], ladder[-1]

    def reader(**target):
        data = dict(shipped)
        entry = {
            "name": "a-target", "not_live": True, "invoke": "command", "command": "a-command",
            "advances": last, "grouping": "none", "requires_role": "none", "publishes": False,
            "batch": "a-batch {deploy:purpose}", **target,
        }
        data["deploy"] = [{key: value for key, value in entry.items() if value is not None}]
        return config.load_text(yaml.safe_dump(data), config.EXAMPLES)

    asked: list = []

    def tracker(configuration, items=None, *, failing=False, at_limit=False):
        def search(terms=None, *, labels=None, fields=None, limit=100):
            asked.append(limit)
            if failing:
                raise port.HostUnavailable("planted")
            return {"items": items, "at_limit": at_limit, "limit": limit}
        return port.Port(configuration, port.port_spec(), adapter=port.Adapter(
            {} if items is None and not failing else {"search_items": search}))

    def item(number, role):
        return {"number": number, "title": f"item {number}", "status": words[role]}

    backlog_items = [item(1, first), item(2, early), item(3, landed), item(4, landed),
                     item(5, last), {"number": 6, "title": "unplaced", "status": "no-such"}]
    runs: list = []

    def printing(*lines, status=0):
        def ran(command, where, given):
            runs.append((command, where, given))
            return status, "".join(f"{line}\n" for line in lines), "planted stderr"
        return ran

    def answered(configuration, ran, items=backlog_items, commit=None, choose=None, **kw):
        resolved = configuration.deploy_batch("a-target", choose, commit)
        subject = tracker(configuration, items, **kw)
        return answer(subject, resolved, backlog(subject), ran)

    def stopped(call) -> bool:
        try:
            call()
        except Stop:
            return True
        return False

    print("What the command is handed:")
    runs.clear()
    got = answered(reader(), printing("3", "#5", "9"))
    advance = got["purposes"][0]
    check("the bound is this module's own", asked[-1] == LIMIT, asked)
    check("an advance hands the items in the role immediately before the one it advances to",
          advance["handed_roles"] == [landed] and advance["handed"] == ["3", "4"], advance)
    check("the handed identifiers arrive on the command's input, one per line",
          runs[-1][2] == "3\n4\n", runs)
    check("and the purpose reaches the command where it places it",
          runs[-1][0] == "a-batch advance", runs)
    check("the command runs in the directory the reader resolved",
          runs[-1][1] == os.path.normpath(os.path.join(config.EXAMPLES, ".")), runs)

    print("What its answer is matched against:")
    check("what it returned and was handed is carried", advance["carried"] == ["3"], advance)
    check("an item in the role it did not return is named, with its title",
          advance["not_returned"] == [{"item": "4", "title": "item 4", "role": landed}], advance)
    check("an identifier it returned and was not handed is named",
          advance["not_handed"] == ["#5", "9"], advance)
    check("a returned identifier is matched whether or not it carries a `#`",
          answered(reader(), printing("#3"))["purposes"][0]["carried"] == ["#3"])
    got = answered(reader(), printing("6"))
    check("a returned item the port could not place is named as unplaced",
          [one["item"] for one in got["purposes"][0]["unplaced_returned"]] == ["6"], got)

    print("The precondition:")
    runs.clear()
    got = answered(reader(requires_role=landed), printing("1", "3"))
    purposes = {row["purpose"]: row for row in got["purposes"]}
    check("a bar over no grouping runs the command a second time, for the precondition",
          list(purposes) == ["advance", "precondition"], got)
    bar = purposes.get("precondition", {})
    check("it hands every item short of the bar, never only the ones the advance draws from",
          bar.get("handed_roles") == [first, early] and bar.get("handed") == ["1", "2"], bar)
    check("and what it returns of those is what holds the target",
          bar.get("carried") == ["1"], bar)
    check("the purpose is told apart on the command line",
          [one[0] for one in runs] == ["a-batch advance", "a-batch precondition"], runs)

    print("The run's own inputs:")
    runs.clear()
    commit = "0123abcd"
    chosen = reader(
        command="ship {choose:scope}",
        choices=[{"name": "scope", "values": ["some", "all"], "default": "some"}],
        batch="carried {deploy:target} {deploy:commit} {choose:scope}",
    )
    answered(chosen, printing(), commit=commit, choose=["scope=all"])
    check("the target, the commit and the run's choice reach the command",
          runs[-1][0] == f"carried a-target {commit} all", runs)
    runs.clear()
    answered(reader(batch="carried"), printing("3"))
    check("a command placing nothing runs as written and is still handed the identifiers",
          runs[-1][0] == "carried" and runs[-1][2] == "3\n4\n", runs)

    print("What the backlog read cannot answer:")
    got = answered(reader(), printing("3", "9"), items=None)
    row = got["purposes"][0]
    check("a tracker with no search hands nothing and carries what the command returned",
          row["carried"] == ["3", "9"] and row["not_returned"] is None
          and got["backlog"].startswith("unread"), got)
    check("a search that failed is a stop",
          stopped(lambda: answered(reader(), printing(), failing=True)))
    got = answered(reader(), printing(), at_limit=True)
    check("a backlog read at its bound says the handed set may be short",
          "may be short" in got["backlog"], got)
    check("a command that failed is a stop, never an empty batch",
          stopped(lambda: answered(reader(), printing("3", status=1))))

    print("A real command:")
    got = answered(reader(batch="cat"), _ran)
    check("a command echoing its input carries exactly the handed set",
          got["purposes"][0]["carried"] == ["3", "4"]
          and got["purposes"][0]["not_returned"] == [], got)

    print("The command line:")
    printed = io.StringIO()
    args = argparse.Namespace(target="a-target", choose=None, commit=None, skills_root=".")
    with redirect_stdout(printed):
        status = run(args, tracker(reader(), backlog_items), reader(), printing("3"))
    check("an answer exits zero and prints the match",
          status == ANSWERED and json.loads(printed.getvalue())["purposes"][0]["carried"] == ["3"],
          printed.getvalue())
    unbatched = reader(advances="none", batch=None)
    with redirect_stdout(io.StringIO()):
        status = run(args, tracker(unbatched, backlog_items), unbatched, printing())
    check("a target carrying no batch exits three", status == NO_BATCH, status)

    print("The role:")
    with open(os.path.join(HERE, "..", "skills", "deploy", "SKILL.md"), encoding="utf-8") as handle:
        role = handle.read()
    check("the deploying role runs this carrier",
          f'/scripts/{os.path.basename(__file__)}" run ' in role)

    print(f"\n{'FAILED' if failures else 'OK'}")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
