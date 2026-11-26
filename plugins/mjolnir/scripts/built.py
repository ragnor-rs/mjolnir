#!/usr/bin/env python3
"""Hold a role's reading of whether an item's work is already built to its shape.

The rule is `plugins/mjolnir/config/schema.md § 42`, which states it and the
argument behind it. Neither is restated here.

⛔ **This module never reads the code.** Which code answers an acceptance bullet
is a reading only the role can take. What is here is the part a carrier can hold:
whether the step runs at a point at all, whether a finding names something real
for every bullet it calls built, what the item's verdict is, and what the role
does next. The verdict is derived here and is never written by hand.

⛔ **It performs nothing.** No item is closed, reopened or rewritten from here,
and a finding that records an act is refused: the step may offer, and what is
offered is a person's to take.

Usage:
    built.py decide --point P       whether the step runs at P, and what a finding
                                    does there (exit 3 where it does not run)
    built.py check --file F         read a finding, refuse a shape § 42 refuses,
                                    and print the verdict and what the role does
    built.py form                   the finding's fields
    built.py --self-test            plant each refused shape and assert the refusal

Exit status: 0 the answer was produced, 1 the finding was refused, 2 the
configuration or the file could not be read, 3 the step does not run at that
point.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config as reader  # noqa: E402 -- the one reader, never a second parser

BUILT, ABSENT, UNESTABLISHED, PARTLY = "built", "absent", "unestablished", "partly built"
BULLET_VERDICTS = (BUILT, ABSENT, UNESTABLISHED)
PROCEED, STOP, ASK = "proceed", "stop", "ask"
OPEN, CLOSED = "open", "closed"
FILE_POINT = "file"

# The finding's form. ⛔ Each field's meaning is § 42's; what is written here is
# only the spelling a role writes and this module reads.
FORM = {
    "item": "the item read, by identifier",
    "point": "where the step ran: one of the points the project names",
    "state": "open | closed -- the item's own state on the tracker",
    "condition": "acceptance | outcome -- what the bullets were read off (§ 4.4)",
    "bullets": "one entry per bullet: {bullet, verdict, and cites | read | why}",
}
BULLET_FORM = {
    BUILT: "cites",
    ABSENT: "read",
    UNESTABLISHED: "why",
}
CITE_KINDS = ("path", "commit", "change")
COMMIT_SHAPE = re.compile(r"^[0-9a-f]{7,40}$")
CHANGE_SHAPE = re.compile(r"^(#\d+|https?://\S+)$")
LINE_SUFFIX = re.compile(r"^(.*?):(\d+)(?:-(\d+))?$")


class FindingError(Exception):
    """A finding § 42 refuses, named so the role can fix it and hand it over again."""


# --- where the step runs ----------------------------------------------------


def decide(resolved, point: str) -> dict:
    """Whether the step runs at `point`, and what a finding does there."""
    points = resolved.get(reader.BUILT_CHECK_POINTS_PATH) or []
    on_finding = resolved.get(f"{reader.BUILT_CHECK_KEY}.on_finding")
    allowed = resolved.facts.get("lists", {}).get(reader.BUILT_CHECK_POINTS_PATH, [])
    if point not in allowed:
        raise FindingError(
            f"`{point}` is not a point; a point is one of {' | '.join(allowed)} (§ 42)."
        )
    runs = point in points
    return {
        "point": point,
        "runs": runs,
        "on_finding": on_finding if runs else None,
        "reason": (
            f"`built_check.points` names `{point}`, so the role reads the code "
            f"before acting, and a finding is handled by `on_finding: {on_finding}` (§ 42)."
            if runs
            else f"`built_check.points` does not name `{point}`, so the role runs no "
            "step here and its reply mentions none (§ 42)."
        ),
    }


# --- the finding ------------------------------------------------------------


def _check_path(root: str, value) -> str:
    if not isinstance(value, str) or not value.strip():
        raise FindingError("a path citation is empty; it names a file in the tree (§ 42).")
    path, first, last = value, None, None
    match = LINE_SUFFIX.match(value)
    if match:
        path, first, last = match.group(1), int(match.group(2)), match.group(3)
    if os.path.isabs(path) or os.path.normpath(path).split(os.sep)[0] == "..":
        raise FindingError(
            f"the path `{value}` is not inside the tree; a citation is repository-relative (§ 42)."
        )
    full = os.path.join(root, path)
    if not os.path.exists(full):
        raise FindingError(
            f"the path `{path}` does not exist in the tree the role is standing in, so the "
            "citation names nothing (§ 42)."
        )
    if first is not None:
        if not os.path.isfile(full):
            raise FindingError(f"`{value}` names a line in `{path}`, which is not a file (§ 42).")
        with open(full, encoding="utf-8", errors="replace") as handle:
            count = sum(1 for _ in handle)
        top = int(last) if last else first
        if first < 1 or top < first or top > count:
            raise FindingError(
                f"`{value}` names lines `{path}` does not have; it has {count} (§ 42)."
            )
    return f"path {value}"


def _check_commit(root: str, value) -> str:
    if not isinstance(value, str) or not COMMIT_SHAPE.match(value):
        raise FindingError(
            f"the commit `{value}` is not a commit name; it is 7 to 40 lowercase hex (§ 42)."
        )
    probe = subprocess.run(
        ["git", "-C", root, "cat-file", "-e", f"{value}^{{commit}}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if probe.returncode != 0:
        raise FindingError(
            f"the commit `{value}` does not resolve in this repository, so the citation "
            "names nothing (§ 42)."
        )
    return f"commit {value}"


def _check_change(_root: str, value) -> str:
    # ⚠️ The host is not asked: a change is held to its form only, which § 42
    # states. A path and a commit are read locally and need no credential.
    if not isinstance(value, str) or not CHANGE_SHAPE.match(value):
        raise FindingError(
            f"the change `{value}` is neither `#<number>` nor an address (§ 42)."
        )
    return f"change {value}"


CITE_CHECKS = {"path": _check_path, "commit": _check_commit, "change": _check_change}


def _check_bullet(root: str, index: int, entry) -> dict:
    where = f"bullet {index + 1}"
    if not isinstance(entry, dict):
        raise FindingError(f"{where} is not a mapping of `bullet`, `verdict` and its evidence (§ 42).")
    text = entry.get("bullet")
    if not isinstance(text, str) or not text.strip():
        raise FindingError(f"{where} states no bullet; each entry carries the bullet it read (§ 42).")
    verdict = entry.get("verdict")
    if verdict not in BULLET_VERDICTS:
        raise FindingError(
            f"{where} has verdict {verdict!r}; a bullet's verdict is one of "
            f"{' | '.join(BULLET_VERDICTS)} (§ 42)."
        )
    evidence_key = BULLET_FORM[verdict]
    extra = set(entry) - {"bullet", "verdict", evidence_key}
    if extra:
        raise FindingError(
            f"{where} carries {sorted(extra)}, which a `{verdict}` bullet does not; it carries "
            f"`{evidence_key}` (§ 42)."
        )
    evidence = entry.get(evidence_key)
    if verdict == BUILT:
        if not isinstance(evidence, list) or not evidence:
            raise FindingError(
                f"{where} is `built` and cites nothing; a built bullet names the path, commit "
                "or change that answers it (§ 42)."
            )
        named = []
        for cite in evidence:
            if not isinstance(cite, dict) or len(cite) != 1 or next(iter(cite)) not in CITE_KINDS:
                raise FindingError(
                    f"{where} cites {cite!r}; a citation is one of "
                    f"{' | '.join(CITE_KINDS)}, written as a one-key mapping (§ 42)."
                )
            kind, value = next(iter(cite.items()))
            try:
                named.append(CITE_CHECKS[kind](root, value))
            except FindingError as error:
                raise FindingError(f"{where}: {error}") from None
        return {"bullet": text, "verdict": verdict, "cites": named}
    if not isinstance(evidence, str) or not evidence.strip():
        what = "what was read" if verdict == ABSENT else "what could not be read, and why"
        raise FindingError(f"{where} is `{verdict}` and does not say {what} (§ 42).")
    return {"bullet": text, "verdict": verdict, evidence_key: evidence}


def item_verdict(bullets: list) -> str:
    """§ 42's derivation, from the bullets and from nothing else."""
    verdicts = {entry["verdict"] for entry in bullets}
    if verdicts == {BUILT}:
        return BUILT
    if verdicts == {ABSENT}:
        return ABSENT
    if BUILT in verdicts:
        return PARTLY
    return UNESTABLISHED


def check(finding, resolved, root: str) -> dict:
    """Refuse a shape § 42 refuses; otherwise the verdict and what the role does."""
    if not isinstance(finding, dict):
        raise FindingError("the finding is not a mapping of the form's fields (§ 42).")
    if "performed" in finding:
        raise FindingError(
            "the finding records an act it performed; the step closes, reopens and rewrites "
            "nothing, and what it may do is offer (§ 42)."
        )
    extra = set(finding) - set(FORM)
    if extra:
        raise FindingError(f"the finding carries {sorted(extra)}, which the form does not (§ 42).")
    missing = [field for field in FORM if field not in finding]
    if missing:
        raise FindingError(f"the finding does not carry {missing} (§ 42).")
    if not str(finding["item"]).strip():
        raise FindingError("the finding names no item (§ 42).")
    point = finding["point"]
    decided = decide(resolved, point)
    if not decided["runs"]:
        raise FindingError(
            f"the finding is for `{point}`, where this project runs no step; a finding nobody "
            "configured is not handed to a role (§ 42)."
        )
    if finding["state"] not in (OPEN, CLOSED):
        raise FindingError(f"the state {finding['state']!r} is neither `open` nor `closed` (§ 42).")
    if finding["condition"] not in ("acceptance", "outcome"):
        raise FindingError(
            f"the condition {finding['condition']!r} is neither `acceptance` nor `outcome` (§ 42)."
        )
    raw = finding["bullets"]
    if not isinstance(raw, list) or not raw:
        raise FindingError("the finding reads no bullet; an item is read bullet by bullet (§ 42).")
    if finding["condition"] == "outcome" and len(raw) != 1:
        raise FindingError(
            "the finding reads an item's outcome as several bullets; an item stating no "
            "acceptance condition is read as one (§ 42)."
        )
    bullets = [_check_bullet(root, index, entry) for index, entry in enumerate(raw)]
    verdict = item_verdict(bullets)

    offers: list[str] = []
    if point == FILE_POINT and finding["state"] == CLOSED and verdict in (ABSENT, PARTLY):
        offers = [f"reopen item {finding['item']}", "file the request anew"]
        does = ASK
    elif verdict == ABSENT:
        does = PROCEED
    elif decided["on_finding"] == "stop":
        does = STOP
    else:
        does = PROCEED
    return {
        "holds": True,
        "item": str(finding["item"]),
        "point": point,
        "verdict": verdict,
        "does": does,
        "offers": offers,
        "performed": "nothing",
        "bullets": bullets,
    }


# --- the command ------------------------------------------------------------


def _load_finding(path: str):
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def main(argv: list) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--skills-root", default=".")
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="command")
    decide_parser = sub.add_parser("decide")
    decide_parser.add_argument("--point", required=True)
    check_parser = sub.add_parser("check")
    check_parser.add_argument("--file", required=True)
    check_parser.add_argument(
        "--root", help="the tree a path citation is read in; the code root where unstated"
    )
    sub.add_parser("form")
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.command == "form":
        print(json.dumps({"fields": FORM, "bullet_evidence": BULLET_FORM,
                          "cites": list(CITE_KINDS)}, indent=2, ensure_ascii=False))
        return 0
    if args.command not in ("decide", "check"):
        parser.print_usage(sys.stderr)
        return 2
    try:
        resolved = reader.load(args.skills_root)
    except reader.ConfigError as error:
        print(str(error), file=sys.stderr)
        return 2
    try:
        if args.command == "decide":
            answer = decide(resolved, args.point)
            print(json.dumps(answer, indent=2, ensure_ascii=False))
            return 0 if answer["runs"] else 3
        try:
            finding = _load_finding(args.file)
        except (OSError, ValueError) as error:
            print(f"the finding could not be read: {error}", file=sys.stderr)
            return 2
        answer = check(finding, resolved, args.root or resolved.code_root)
    except FindingError as error:
        print(json.dumps({"holds": False, "refused": str(error)}, indent=2, ensure_ascii=False))
        return 1
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    return 0


# --- the suite --------------------------------------------------------------


def _resolved(block: str | None):
    """The none example, with § 42's block replaced by `block` where one is given."""
    example = os.path.join(HERE, "..", "config", "examples", "none.yaml")
    with open(example, encoding="utf-8") as handle:
        text = handle.read()
    text = re.sub(r"(?m)^built_check:\n(?:  .*\n)*", "", text)
    if block is not None:
        text += "\n" + block
    return reader.load_text(text, os.path.dirname(example), check_paths=False)


def self_test() -> int:
    failures = 0

    def check_that(name: str, ok: bool, detail: str = "") -> None:
        nonlocal failures
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}" + ("" if ok else f": {detail}"))
        if not ok:
            failures += 1

    def refused(finding, resolved, root, fragment: str) -> tuple[bool, str]:
        try:
            answer = check(finding, resolved, root)
        except FindingError as error:
            return fragment in str(error), str(error)
        return False, f"held: {answer}"

    with tempfile.TemporaryDirectory() as root:
        subprocess.run(["git", "init", "-q", root], check=True)
        os.makedirs(os.path.join(root, "src"))
        with open(os.path.join(root, "src", "feature.py"), "w", encoding="utf-8") as handle:
            handle.write("def feature():\n    return 1\n")
        for args in (["add", "."], ["-c", "user.name=t", "-c", "user.email=t@t",
                                    "commit", "-q", "-m", "one"]):
            subprocess.run(["git", "-C", root, *args], check=True)
        head = subprocess.run(["git", "-C", root, "rev-parse", "HEAD"], capture_output=True,
                              text=True, check=True).stdout.strip()

        nowhere = _resolved(None)
        report = _resolved("built_check:\n  points: [file, start, implement]\n")
        stop = _resolved("built_check:\n  points: [start, file]\n  on_finding: stop\n")

        print("Where the step runs:")
        for point in ("file", "start", "implement"):
            check_that(f"an unstated block runs no step at `{point}`",
                       decide(nowhere, point)["runs"] is False)
        check_that("a named point runs, with its finding handled by `on_finding`",
                   decide(stop, "start") == {**decide(stop, "start"), "runs": True,
                                             "on_finding": "stop"})
        check_that("a point the project does not name runs nothing",
                   decide(stop, "implement")["runs"] is False)
        try:
            decide(report, "deploy")
            check_that("a name outside the points is refused", False, "decided")
        except FindingError:
            check_that("a name outside the points is refused", True)

        def finding(**over):
            base = {"item": "7", "point": "start", "state": OPEN, "condition": "acceptance",
                    "bullets": [{"bullet": "a feature", "verdict": BUILT,
                                 "cites": [{"path": "src/feature.py:1-2"}, {"commit": head},
                                           {"change": "#12"}]}]}
            base.update(over)
            return base

        print("\nThe green side:")
        answer = check(finding(), report, root)
        check_that("a built bullet citing a real path, commit and change holds",
                   answer["verdict"] == BUILT and answer["does"] == PROCEED, f"{answer}")
        check_that("⛔ and nothing is performed", answer["performed"] == "nothing")

        print("\nEach shape § 42 refuses, planted:")
        planted = [
            ("a built bullet citing nothing", finding(bullets=[
                {"bullet": "b", "verdict": BUILT, "cites": []}]), "cites nothing"),
            ("a built bullet with no citation key", finding(bullets=[
                {"bullet": "b", "verdict": BUILT}]), "cites nothing"),
            ("a path that does not exist", finding(bullets=[
                {"bullet": "b", "verdict": BUILT, "cites": [{"path": "src/missing.py"}]}]),
             "does not exist"),
            ("a path outside the tree", finding(bullets=[
                {"bullet": "b", "verdict": BUILT, "cites": [{"path": "../feature.py"}]}]),
             "not inside the tree"),
            ("a line the file does not have", finding(bullets=[
                {"bullet": "b", "verdict": BUILT, "cites": [{"path": "src/feature.py:9"}]}]),
             "does not have"),
            ("a commit that does not resolve", finding(bullets=[
                {"bullet": "b", "verdict": BUILT, "cites": [{"commit": "deadbeef"}]}]),
             "does not resolve"),
            ("a change in no form", finding(bullets=[
                {"bullet": "b", "verdict": BUILT, "cites": [{"change": "the PR"}]}]),
             "neither"),
            ("a citation of an unknown kind", finding(bullets=[
                {"bullet": "b", "verdict": BUILT, "cites": [{"memory": "I recall it"}]}]),
             "a citation is one of"),
            ("an unestablished bullet with no reason", finding(bullets=[
                {"bullet": "b", "verdict": UNESTABLISHED}]), "could not be read"),
            ("an absent bullet that says nothing was read", finding(bullets=[
                {"bullet": "b", "verdict": ABSENT, "read": " "}]), "what was read"),
            ("a verdict outside the three", finding(bullets=[
                {"bullet": "b", "verdict": "done", "cites": [{"change": "#1"}]}]), "verdict"),
            ("an absent bullet carrying a citation", finding(bullets=[
                {"bullet": "b", "verdict": ABSENT, "read": "x", "cites": [{"change": "#1"}]}]),
             "does not"),
            ("a finding recording an act it performed",
             {**finding(), "performed": ["closed item 7"]}, "closes, reopens and rewrites"),
            ("a field outside the form", {**finding(), "verdict": BUILT}, "the form does not"),
            ("a finding reading no bullet", finding(bullets=[]), "no bullet"),
            ("an outcome read as several bullets", finding(condition="outcome", bullets=[
                {"bullet": "a", "verdict": ABSENT, "read": "x"},
                {"bullet": "b", "verdict": ABSENT, "read": "x"}]), "read as one"),
            ("a finding at a point the project does not run", finding(point="implement"),
             "runs no step"),
        ]
        for name, planted_finding, fragment in planted:
            resolved = stop if name.endswith("does not run") else report
            ok, said = refused(planted_finding, resolved, root, fragment)
            check_that(f"{name} is refused", ok, said)

        print("\nThe verdict, derived:")
        b = {"bullet": "x", "verdict": BUILT, "cites": [{"change": "#1"}]}
        a = {"bullet": "y", "verdict": ABSENT, "read": "src/"}
        u = {"bullet": "z", "verdict": UNESTABLISHED, "why": "the module is generated"}
        for name, bullets, expected in (
            ("every bullet built", [b, b], BUILT),
            ("every bullet absent", [a, a], ABSENT),
            ("built beside absent", [b, a], PARTLY),
            ("built beside unestablished", [b, u], PARTLY),
            ("absent beside unestablished, which is never read as absent", [a, u], UNESTABLISHED),
            ("every bullet unestablished", [u], UNESTABLISHED),
        ):
            got = check(finding(bullets=bullets), report, root)["verdict"]
            check_that(f"{name} reads `{expected}`", got == expected, f"read {got!r}")

        print("\nWhat the role does:")
        for name, resolved, over, expected in (
            ("partly built under `report` carries on", report, {"bullets": [b, a]}, PROCEED),
            ("partly built under `stop` stops", stop, {"bullets": [b, a]}, STOP),
            ("built under `stop` stops", stop, {"bullets": [b]}, STOP),
            ("absent carries on even under `stop`", stop, {"bullets": [a]}, PROCEED),
            ("unestablished under `stop` stops", stop, {"bullets": [u]}, STOP),
        ):
            got = check(finding(**over), resolved, root)["does"]
            check_that(name, got == expected, f"did {got!r}")

        print("\nA closed item at filing:")
        closed_absent = check(finding(point="file", state=CLOSED, bullets=[a]), report, root)
        check_that("a closed item whose work is absent is offered for reopening beside filing anew",
                   closed_absent["does"] == ASK
                   and closed_absent["offers"] == ["reopen item 7", "file the request anew"],
                   f"{closed_absent}")
        closed_partly = check(finding(point="file", state=CLOSED, bullets=[b, a]), report, root)
        check_that("and so is one whose work is partly built",
                   closed_partly["does"] == ASK and len(closed_partly["offers"]) == 2,
                   f"{closed_partly}")
        closed_built = check(finding(point="file", state=CLOSED, bullets=[b]), report, root)
        check_that("a closed item whose work is built is offered nothing",
                   closed_built["offers"] == [] and closed_built["does"] == PROCEED,
                   f"{closed_built}")
        started_closed = check(finding(state=CLOSED, bullets=[a]), report, root)
        check_that("the offer is the filing point's alone",
                   started_closed["offers"] == [], f"{started_closed}")
        every = [closed_absent, closed_partly, closed_built, started_closed]
        check_that("⛔ no answer performs anything",
                   all(answer["performed"] == "nothing" for answer in every))

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
