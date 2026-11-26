#!/usr/bin/env python3
"""Read a deploy's check figures, and lower an outcome only where a bound says so.

The rule is `plugins/mjolnir/config/schema.md § 33 → A check's figures, and the
bound that lets one decide anything`, which states it. It is not restated here.
⛔ What this file performs:

  every figure a target's `figures` entry names comes back with its value, or
  as **unread** with the reason -- a command that exited non-zero, a line the
  grammar cannot read, one name printed twice, or a figure nobody printed;

  a figure **with a bound** lowers the outcome handed for its check -- `passed`
  to `failed` outside the bound, `passed` to `unread` where the figure is unread
  -- and **no figure without one decides anything**.

⛔ Every value is **read from the configuration**: which checks carry figures,
the command printing each check's figures, the figures expected and the bounds.
No runner, report format or project appears in this file; the command is the
project's own and this file reads only its output, in the form § 33 states.

⚠️ **The commands run through a shell, at the target's code root**, for the
reason `executed.py` gives for § 16's: the contract is a command ending in
whatever turns a runner's output into the stated form, which is a pipeline, and
it is the project's own configuration -- the same trust as `host.checks`.

Usage:
    figures.py --target NAME [--reading CHECK=OUTCOME ...] [--skills-root DIR]
                                read that target's figures and print them with
                                the outcomes to hand to `config.py --advance-for`
    figures.py --self-test      assert each rule reddens on its planted
                                violation and reads real commands, then stop
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config as reader  # noqa: E402 -- the one reader of the surface

UNREAD = reader.ADVANCE_UNREPORTED
PASSED = reader.ADVANCE_RELEASES
FAILED = reader.ADVANCE_DEFAULT_HOLDS


class Unreadable(Exception):
    """A command's figures could not be read, with the reason."""


def run_command(command: str, root: str) -> str:
    """The command's standard output, or `Unreadable` naming why there is none.

    ⚠️ **A non-zero exit refuses the reading**: a verification that failed may
    have printed figures about the part it reached, and reporting them as the
    check's figures would report a number about a run nobody finished.
    """
    try:
        done = subprocess.run(
            command,
            shell=True,
            cwd=root,
            capture_output=True,
            text=True,
            errors="replace",
            check=False,
        )
    except OSError as exc:
        raise Unreadable(f"the command could not be run: {exc}") from exc
    if done.returncode != 0:
        raise Unreadable(f"the command exited {done.returncode}")
    return done.stdout


def parse(output: str) -> dict[str, float]:
    """`<name> <number>` lines into one mapping, or `Unreadable`.

    ⛔ **A line the grammar cannot read refuses the whole output**, and so does
    one name printed twice: a line nobody can parse may be the figure, and two
    values for one name leave which of them is the figure undefined.
    """
    figures: dict[str, float] = {}
    for number, line in enumerate(output.splitlines(), start=1):
        text = line.strip()
        if not text:
            continue
        match = reader.FIGURE_LINE.fullmatch(text)
        if match is None:
            raise Unreadable(
                f"line {number} is not `<name> <number>`: {text[:80]!r}"
            )
        name, value = match.group(1), match.group(2)
        if name in figures:
            raise Unreadable(f"line {number} prints {name!r} a second time")
        figures[name] = float(value) if "." in value else int(value)
    return figures


def outside(value: float, bound: dict) -> bool:
    """Whether a value falls outside a bound's `min` and `max`, both inclusive."""
    return ("min" in bound and value < bound["min"]) or (
        "max" in bound and value > bound["max"]
    )


def judge(entry: dict, readings: dict[str, str], printed: dict) -> dict:
    """§ 33's verdict over one target's figures.

    `printed` maps each `figures` entry's check to what its command printed,
    or to the `Unreadable` it raised. ⛔ **A bound only ever lowers an outcome**,
    and a check handed no outcome is handed none still.
    """
    figures = []
    out = dict(readings)
    report = []
    for block in entry.get(reader.FIGURES) or ():
        check = block["check"]
        got = printed[check]
        failure = str(got) if isinstance(got, Unreadable) else None
        values = {} if failure else got
        bounds = {
            bound["figure"]: bound for bound in block.get(reader.FIGURE_BOUNDS) or ()
        }
        lowered_to = None
        for name in block["names"]:
            value = values.get(name)
            bound = bounds.get(name)
            if value is None:
                why = failure or "the command did not print it"
                state = UNREAD
            else:
                why = None
                state = "outside" if bound and outside(value, bound) else "read"
            figures.append({
                "check": check,
                "figure": name,
                "value": value,
                "unread_because": why,
                "bound": {k: v for k, v in (bound or {}).items() if k != "figure"} or None,
                "decides": bound is not None,
            })
            if bound is None:
                continue
            if state == "outside":
                lowered_to = FAILED
            elif state == UNREAD and lowered_to is None:
                lowered_to = UNREAD
        for name, value in values.items():
            if name not in block["names"]:
                figures.append({
                    "check": check, "figure": name, "value": value,
                    "unread_because": None, "bound": None, "decides": False,
                })
        if lowered_to and out.get(check) == PASSED:
            out[check] = lowered_to
            report.append(
                f"{check!r} was handed `passed` and a bounded figure reads "
                + ("outside its bound" if lowered_to == FAILED else "unread")
                + f", so it is handed on as `{lowered_to}` (§ 33)."
            )
        elif lowered_to and check not in out:
            report.append(
                f"{check!r} has a bounded figure reading "
                + ("outside its bound" if lowered_to == FAILED else "unread")
                + " and was handed no outcome; it is handed none still, which "
                "`--advance-for` reads as `unread` (§ 33)."
            )
        if failure:
            report.append(f"{check!r}: every figure is unread, because {failure}.")
    if not entry.get(reader.FIGURES):
        report.append(
            f"The target {entry.get('name')!r} states no `figures`, so no figure is "
            "read and every outcome is handed on as it came (§ 33) -- which says "
            "nothing about whether a check reported any."
        )
    return {
        "target": entry.get("name"),
        "figures": figures,
        "readings": out,
        "report": report,
    }


def read(config, target: str, readings: dict[str, str]) -> dict:
    """Run the target's figure commands at its code root and judge them."""
    stated = [
        e for e in config.get("deploy") or ()
        if isinstance(e, dict) and e.get("name") == target
    ]
    if not stated:
        raise reader.ConfigError(
            "deploy", f"names no target {target!r} (§ 33), so there are no figures to read."
        )
    entry = stated[0]
    for name, outcome in readings.items():
        if outcome not in reader.ADVANCE_OUTCOMES:
            raise reader.ConfigError(
                f"deploy[{target}].{reader.FIGURES}",
                f"was handed {outcome!r} for {name!r}; the outcomes § 33 states are "
                f"{' | '.join(reader.ADVANCE_OUTCOMES)}.",
            )
    root = (
        config.root(entry["code_root"]).code_root
        if entry.get("code_root") else config.code_root
    )
    printed = {}
    for block in entry.get(reader.FIGURES) or ():
        try:
            printed[block["check"]] = parse(run_command(block["reads"], root))
        except Unreadable as exc:
            printed[block["check"]] = exc
    return judge(entry, readings, printed)


# --------------------------------------------------------------------------
# Self-test
# --------------------------------------------------------------------------


def _self_test() -> int:
    failures = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if ok else 'FAIL'}  {name}")
        if not ok:
            failures.append(f"{name}: {detail}")

    def entry(**block) -> dict:
        base = {"check": "smoke", "reads": "unused", "names": ["cases", "score"]}
        base.update(block)
        return {"name": "staging", reader.FIGURES: [base]}

    print("§ 33, the figure line's grammar:")
    check("two figures, an integer and a decimal, are read",
          parse("cases 12\nscore 0.75\n") == {"cases": 12, "score": 0.75})
    check("blank lines are read as nothing", parse("\ncases 3\n\n") == {"cases": 3})
    for label, text in (
        ("a line with no number refuses the output", "cases twelve\n"),
        ("a line with two numbers refuses the output", "cases 1 2\n"),
        ("a name of two words refuses the output", "case count 3\n"),
        ("one name printed twice refuses the output", "cases 1\ncases 2\n"),
    ):
        try:
            parse(text)
        except Unreadable:
            check(label, True)
        else:
            check(label, False, "read")

    print("\n§ 33, what a figure does to an outcome:")
    plain = judge(entry(), {"smoke": "passed"}, {"smoke": {"cases": 0, "score": 0.1}})
    check("no figure without a bound decides anything, even zero cases",
          plain["readings"] == {"smoke": "passed"}, f"{plain['readings']}")
    check("every named figure is reported with its value",
          [(f["figure"], f["value"]) for f in plain["figures"]]
          == [("cases", 0), ("score", 0.1)], f"{plain['figures']}")
    missing = judge(entry(), {"smoke": "passed"}, {"smoke": {"cases": 4}})
    unread = [f for f in missing["figures"] if f["value"] is None]
    check("a named figure the command did not print is reported unread, with why",
          len(unread) == 1 and unread[0]["figure"] == "score"
          and unread[0]["unread_because"], f"{missing['figures']}")
    extra = judge(entry(), {}, {"smoke": {"cases": 4, "score": 1, "flaky": 2}})
    check("a printed figure the entry does not name is reported and decides nothing",
          any(f["figure"] == "flaky" and not f["decides"] for f in extra["figures"]),
          f"{extra['figures']}")
    refused = judge(entry(), {"smoke": "passed"}, {"smoke": Unreadable("the command exited 2")})
    check("an unreadable command leaves every named figure unread with its reason",
          all(f["value"] is None and "exited 2" in f["unread_because"]
              for f in refused["figures"]), f"{refused['figures']}")

    bounded = entry(bounds=[{"figure": "cases", "min": 10}])
    low = judge(bounded, {"smoke": "passed"}, {"smoke": {"cases": 3, "score": 1}})
    check("a passed check whose bounded figure is below its min is handed on failed",
          low["readings"]["smoke"] == FAILED, f"{low['readings']}")
    high = judge(entry(bounds=[{"figure": "score", "max": 0.5}]), {"smoke": "passed"},
                 {"smoke": {"cases": 3, "score": 0.9}})
    check("a passed check whose bounded figure is above its max is handed on failed",
          high["readings"]["smoke"] == FAILED, f"{high['readings']}")
    inside = judge(bounded, {"smoke": "passed"}, {"smoke": {"cases": 10, "score": 1}})
    check("a bounded figure on its bound keeps the outcome",
          inside["readings"]["smoke"] == PASSED, f"{inside['readings']}")
    gone = judge(bounded, {"smoke": "passed"}, {"smoke": {"score": 1}})
    check("a passed check whose bounded figure is unread is handed on unread",
          gone["readings"]["smoke"] == UNREAD, f"{gone['readings']}")
    kept = judge(bounded, {"smoke": "skipped"}, {"smoke": {"cases": 3}})
    check("a bound never changes an outcome that was not passed",
          kept["readings"]["smoke"] == "skipped", f"{kept['readings']}")
    unhanded = judge(bounded, {}, {"smoke": {"cases": 3}})
    check("a check handed no outcome is handed none still",
          "smoke" not in unhanded["readings"], f"{unhanded['readings']}")
    both = judge(entry(bounds=[{"figure": "cases", "min": 1},
                               {"figure": "score", "min": 0.5}]),
                 {"smoke": "passed"}, {"smoke": {"cases": 5}})
    check("one bounded figure unread and another inside lowers to unread",
          both["readings"]["smoke"] == UNREAD, f"{both['readings']}")
    worse = judge(entry(bounds=[{"figure": "cases", "min": 10},
                                {"figure": "score", "min": 0.5}]),
                  {"smoke": "passed"}, {"smoke": {"cases": 5}})
    check("a figure outside its bound outweighs another that is unread",
          worse["readings"]["smoke"] == FAILED, f"{worse['readings']}")
    other = judge(bounded, {"smoke": "passed", "e2e": "passed"}, {"smoke": {"cases": 1}})
    check("a bound lowers its own check and no other",
          other["readings"]["e2e"] == PASSED, f"{other['readings']}")
    none = judge({"name": "staging"}, {"smoke": "passed"}, {})
    check("a target stating no figures hands every outcome on as it came, and says so",
          none["readings"] == {"smoke": "passed"} and none["figures"] == []
          and any("states no `figures`" in line for line in none["report"]),
          f"{none}")

    print("\n§ 33, real commands run in a directory this suite builds:")
    with tempfile.TemporaryDirectory() as root:
        with open(os.path.join(root, "report.txt"), "w", encoding="utf-8") as handle:
            handle.write("cases 42\nscore 0.9\n")
        check("a command reading a file at the root it runs in is read",
              parse(run_command("cat report.txt", root)) == {"cases": 42, "score": 0.9})
        try:
            run_command("cat report.txt; exit 3", root)
        except Unreadable as exc:
            check("a command exiting non-zero is unread, whatever it printed",
                  "exited 3" in str(exc), str(exc))
        else:
            check("a command exiting non-zero is unread, whatever it printed", False, "read")

        class _Loaded:
            """The two readings `read` takes of a loaded configuration."""
            code_root = root

            def get(self, path):
                return [{"name": "staging", reader.FIGURES: [{
                    "check": "smoke", "reads": "cat report.txt",
                    "names": ["cases", "score"],
                    reader.FIGURE_BOUNDS: [{"figure": "cases", "min": 100}],
                }]}] if path == "deploy" else None

        whole = read(_Loaded(), "staging", {"smoke": "passed"})
        check("a target's own command is run at its code root and its bound applied",
              whole["readings"] == {"smoke": FAILED}
              and [f["value"] for f in whole["figures"]] == [42, 0.9], f"{whole}")
        try:
            read(_Loaded(), "staging", {"smoke": "green"})
        except reader.ConfigError:
            check("an outcome outside § 33's table is refused rather than read", True)
        else:
            check("an outcome outside § 33's table is refused rather than read", False, "read")

    print()
    if failures:
        print(f"{len(failures)} failure(s):")
        for failure in failures:
            print(f"  - {failure}")
        return 1
    print("every check passed")
    return 0


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--target", help="one of § 33's deploy targets, by name")
    parser.add_argument(
        "--reading", action="append", default=[], metavar="CHECK=OUTCOME",
        help="one check's outcome as the verification reported it, repeated per check",
    )
    parser.add_argument("--skills-root", default=".")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return _self_test()
    if not args.target:
        parser.error("--target is required")
    try:
        config = reader.load(args.skills_root)
        readings = reader._parse_readings(args.reading)
        answer = read(config, args.target, readings)
    except reader.ConfigError as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
