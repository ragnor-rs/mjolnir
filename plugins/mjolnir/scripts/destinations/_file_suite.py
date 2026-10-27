#!/usr/bin/env python3
"""The file destination's own decisions, held against a real directory.

What the contract's suite holds is the contract -- the operation list, the absent
case, a kind of `none`. This holds what the implementation beside it decided, and
each of those is reachable only by writing files: the path § 9 fixed, a rebuild
that leaves one entry, a hand-edited entry reported rather than counted as
nothing, a period read per day, and the two directories that are refused.

⛔ **Every write lands in a temporary directory the suite makes and removes**, and
the configuration is built over it. Nothing here touches the project's own store:
an entry written beside a real one would be a day this repository's own log claims
and nobody worked.

⚠️ **The port is what every call goes through**, never the module's functions
directly. The adapter resolves no project for itself, so a direct call would
bypass the one place a configuration is bound -- and the suite would be exercising
a path no role takes.

Usage:
    _file_suite.py    hold the file destination to its own decisions
"""

from __future__ import annotations

import os
import sys
import tempfile

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import config  # noqa: E402
import port  # noqa: E402
from destinations import file as implementation  # noqa: E402

# The port this suite drives, read off the surface rather than written out.
PORT = "day_log.destination.kind"

# Two days far enough apart that a range can exclude one. ⚠️ Fixed rather than
# taken from the clock: a suite whose fixture is today is a suite whose failures
# depend on when it ran.
A_DAY = "2026-03-04"
NEXT_DAY = "2026-03-05"
A_LATER_DAY = "2026-04-01"


def _configuration(out_dir: str, root: str) -> config.Config:
    """A whole example, pointed at a temporary directory and a temporary root.

    Taken from the examples rather than written here, for the reason the
    contract's own suite gives: a fixture written by hand is a second
    configuration, free to disagree with every one this toolkit ships.
    """
    name = sorted(
        entry for entry in os.listdir(config.EXAMPLES) if entry.endswith((".yaml", ".yml"))
    )[0]
    with open(os.path.join(config.EXAMPLES, name), encoding="utf-8") as handle:
        loaded = config.load_text(handle.read(), config.EXAMPLES)
    spec = port.port_spec(PORT)
    node = loaded.data
    for part in spec.prefix.split("."):
        node = node.setdefault(part, {})
    node["kind"] = implementation.KIND
    node[implementation.OUT_DIR] = out_dir
    # ⛔ The code root is pointed somewhere real and separate, because one of the
    # refusals below is about a directory *inside* it: a fixture whose root was
    # the examples directory would make that plant depend on where this repository
    # happens to sit.
    loaded.data["roots"] = {"code": root}
    for view in loaded.views.values():
        view.data["roots"] = {"code": root}
    return loaded


def _port(out_dir: str, root: str) -> port.Port:
    return port.Port(_configuration(out_dir, root), port.port_spec(PORT))


def self_test() -> int:
    failures = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal failures
        if condition:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}{': ' + detail if detail else ''}")

    def refused(call) -> str | None:
        try:
            call()
        except config.ConfigError as error:
            return error.key
        return None

    with tempfile.TemporaryDirectory() as workspace:
        root = os.path.join(workspace, "repository")
        store = os.path.join(workspace, "store")
        os.makedirs(root)
        here = _port(store, root)
        spec = port.port_spec(PORT)

        # Every operation § 25 states is implemented, asserted as a **relation**
        # against the surface's own list rather than as a count or a list of
        # names: a number here would be wrong the next time the section grows.
        check(
            "this store implements every operation the surface states",
            all(here.implements(operation) for operation in here.stated),
            f"absent: {sorted(o for o in here.stated if not here.implements(o))!r}",
        )

        # ⛔ The path § 9 fixed, byte for byte. This is the acceptance condition a
        # project that states no destination is owed, and it is the one assertion
        # here that must never be relaxed to a pattern.
        where = here.invoke("locate", A_DAY)
        check(
            "an entry's path is the directory, the stem, the day and the suffix",
            where.result == os.path.join(store, f"day-report-{A_DAY}.txt"),
            f"located {where.result!r}",
        )
        check(
            "and locating creates nothing",
            not os.path.exists(store),
            f"{store} was created by a read",
        )

        # Nothing recorded yet, which is `None` and not an entry with no hours.
        check(
            "a day with no entry reads as none at all",
            here.invoke("read_day", A_DAY).result is None,
        )

        recorded = here.invoke("append_day", A_DAY, 6.5, "Wrote the thing.")
        check("a day is recorded", recorded.performed, str(recorded))
        check(
            "and lands at the path `locate` named",
            os.path.exists(where.result),
            f"{where.result!r} is not there",
        )
        read = here.invoke("read_day", A_DAY).result
        check(
            "and reads back as the two values it was given",
            read is not None
            and read["hours"] == 6.5
            and read["description"] == "Wrote the thing.",
            f"read {read!r}",
        )

        # ⛔ The acceptance condition § 25 states for every adapter: a rebuilt day
        # leaves **one** entry. Proved by rebuilding a day already recorded and
        # counting what the directory holds, rather than by reading the file --
        # the failure this is about is a second file beside the first.
        rebuilt = here.invoke("replace_day", A_DAY, 7.0, "Wrote it again, shorter.")
        check("a recorded day is rebuilt", rebuilt.performed, str(rebuilt))
        check(
            "and the rebuild leaves one entry for that day",
            sorted(os.listdir(store)) == [f"day-report-{A_DAY}.txt"],
            f"the store holds {sorted(os.listdir(store))!r}",
        )
        read = here.invoke("read_day", A_DAY).result
        check(
            "which carries the new values and no tail of the old",
            read["hours"] == 7.0
            and read["description"] == "Wrote it again, shorter."
            and "Wrote the thing." not in read["text"],
            f"read {read!r}",
        )

        # ⛔ And an append over a recorded day is refused rather than written
        # beside it, which is the doubled total § 25 names.
        check(
            "an append over a day already recorded is refused, naming the key",
            refused(lambda: here.invoke("append_day", A_DAY, 1.0, "Again."))
            == f"{spec.prefix}.{implementation.OUT_DIR}",
            f"reported {refused(lambda: here.invoke('append_day', A_DAY, 1.0, 'x'))!r}",
        )
        check(
            "and the store still holds one entry for it",
            sorted(os.listdir(store)) == [f"day-report-{A_DAY}.txt"],
            f"the store holds {sorted(os.listdir(store))!r}",
        )

        # A period, per day and never a total.
        here.invoke("append_day", NEXT_DAY, 3.0, "Half a day.")
        here.invoke("append_day", A_LATER_DAY, 8.0, "A month later.")
        period = here.invoke("read_hours", A_DAY, NEXT_DAY).result
        check(
            "a period answers per day, both ends included",
            period["hours"] == {A_DAY: 7.0, NEXT_DAY: 3.0},
            f"read {period['hours']!r}",
        )
        check(
            "and a day outside it is not in the answer",
            A_LATER_DAY not in period["hours"],
            f"read {period['hours']!r}",
        )
        check(
            "and the answer carries no total for a consumer to read as one",
            "total" not in period and "sum" not in period,
            f"answered {sorted(period)!r}",
        )
        check(
            "and nothing in that range was unreadable",
            period["unreadable"] == {},
            f"reported {period['unreadable']!r}",
        )
        backwards = refused(lambda: here.invoke("read_hours", NEXT_DAY, A_DAY))
        check(
            "a period read backwards is refused rather than answered empty",
            backwards == f"{spec.prefix}.range",
            f"reported {backwards!r}",
        )

        # ⛔ A day the store holds and cannot read is named, never counted as
        # nothing. Planted by rewriting an entry the way a person correcting a
        # figure by hand would -- which is § 25's rule that what comes back out of
        # a store is data rather than this adapter's own output.
        with open(os.path.join(store, f"day-report-{NEXT_DAY}.txt"), "w", encoding="utf-8") as handle:
            handle.write("three and a half hours, roughly\n\nHalf a day.\n")
        period = here.invoke("read_hours", A_DAY, NEXT_DAY).result
        check(
            "an entry whose hours cannot be read is named as unreadable",
            NEXT_DAY in period["unreadable"],
            f"reported {period['unreadable']!r}",
        )
        check(
            "and is not in the hours it answers with, as zero or otherwise",
            NEXT_DAY not in period["hours"],
            f"read {period['hours']!r}",
        )
        check(
            "while the day beside it still answers",
            period["hours"] == {A_DAY: 7.0},
            f"read {period['hours']!r}",
        )
        # And the same entry read on its own is an entry with no hours rather than
        # no entry: a caller that read the two the same way would append beside it.
        edited = here.invoke("read_day", NEXT_DAY).result
        check(
            "an unreadable entry read on its own is present with no hours",
            edited is not None and edited["hours"] is None,
            f"read {edited!r}",
        )
        check(
            "so an append over it is still refused",
            refused(lambda: here.invoke("append_day", NEXT_DAY, 3.0, "Half a day."))
            == f"{spec.prefix}.{implementation.OUT_DIR}",
        )
        # ⛔ A file whose name is this store's shape and whose day is not a day is
        # reported rather than skipped: it may be the entry a period is missing.
        with open(os.path.join(store, "day-report-the-other-day.txt"), "w", encoding="utf-8") as handle:
            handle.write("Hours worked: 2\n\nSomething.\n")
        period = here.invoke("read_hours", A_DAY, A_LATER_DAY).result
        check(
            "a file named with no readable day is reported, not swept past",
            "day-report-the-other-day.txt" in period["unreadable"],
            f"reported {period['unreadable']!r}",
        )

        # ⛔ A day this store cannot name is refused before anything is written,
        # rather than writing a file no later read finds.
        for given in ("2026-3-4", "yesterday", "2026-03-04T10:00"):
            check(
                f"a day written {given!r} is refused, naming the key",
                refused(lambda day=given: here.invoke("append_day", day, 1.0, "x"))
                == f"{spec.prefix}.day",
                f"reported {refused(lambda day=given: here.invoke('locate', day))!r}",
            )

    # The two directories that are refused, each in a workspace of its own so the
    # refusal is the only thing that could have stopped a write.
    with tempfile.TemporaryDirectory() as workspace:
        root = os.path.join(workspace, "repository")
        os.makedirs(root)
        spec = port.port_spec(PORT)
        # ⛔ No directory stated, which § 25 keeps unrequired and this adapter
        # therefore refuses at the first operation with the key named.
        unset = _port("", root)
        check(
            "no directory stated is refused at the operation, naming the key",
            refused(lambda: unset.invoke("locate", A_DAY))
            == f"{spec.prefix}.{implementation.OUT_DIR}",
            f"reported {refused(lambda: unset.invoke('locate', A_DAY))!r}",
        )
        # ⛔ A directory inside the repository, which § 9 forbids outright. ⚠️ The
        # plant is a path *under* the root rather than the root itself, that being
        # the shape a project would actually write.
        inside = _port(os.path.join(root, "logs"), root)
        check(
            "a directory inside the code root is refused, naming the key",
            refused(lambda: inside.invoke("append_day", A_DAY, 1.0, "x"))
            == f"{spec.prefix}.{implementation.OUT_DIR}",
            f"reported {refused(lambda: inside.invoke('append_day', A_DAY, 1.0, 'x'))!r}",
        )
        check(
            "and nothing was written there",
            not os.path.exists(os.path.join(root, "logs")),
            "the refusal came after the directory was made",
        )
        # And the green side of that scope: a directory beside the repository is
        # accepted, so the refusal above is about being inside one rather than
        # about this adapter refusing every path.
        beside = _port(os.path.join(workspace, "beside"), root)
        check(
            "a directory beside the code root is accepted",
            beside.invoke("append_day", A_DAY, 1.0, "Outside the tree.").performed,
        )
        # ⛔ And the variable a project writes is expanded here, which is what § 11
        # leaves to the role's own command. Planted as a variable the environment
        # does hold, since the point is that expansion happens at all.
        named = _port(os.path.join("$HOME", "..", "nothing-is-written-here"), root)
        located = named.invoke("locate", A_DAY).result
        check(
            "a directory naming a shell variable is expanded by this adapter",
            "$HOME" not in located and located.startswith(os.sep),
            f"located {located!r}",
        )

    # ⛔ A store that cannot be reached, which is the one outcome held apart from
    # every absence above: the capability is present and the call did not go
    # through, so the port answers `failed` with the store's own words and the day
    # is **not** reported as recorded. Planted by taking write permission off the
    # directory rather than by a double, because what is being held is this
    # adapter turning an operating-system failure into the contract's own
    # exception.
    with tempfile.TemporaryDirectory() as workspace:
        root = os.path.join(workspace, "repository")
        sealed = os.path.join(workspace, "sealed")
        os.makedirs(root)
        os.makedirs(sealed)
        os.chmod(sealed, 0o500)
        try:
            unreachable = _port(os.path.join(sealed, "store"), root)
            outcome = unreachable.invoke("append_day", A_DAY, 4.0, "Nowhere to put it.")
            # ⚠️ Asserted as *the plant took* before asserting the behaviour. Run
            # as a user the mode does not bind -- root -- the write succeeds and
            # this whole block would otherwise report green on a plant that never
            # fired, which is the one failure a permission-based plant has.
            check(
                "the sealed directory really refused the write",
                not outcome.performed,
                "the write went through, so this plant asserts nothing about a "
                "store that cannot be reached -- run as a user the directory "
                "mode binds",
            )
            if not outcome.performed:
                check(
                    "a store that cannot be reached comes back failed, not as an absence",
                    outcome.failed and outcome.detail != unreachable.fallback("append_day"),
                    f"got {str(outcome)!r}",
                )
                check(
                    "and the report carries the store's own words",
                    "could not be created" in outcome.detail
                    or "could not be written" in outcome.detail,
                    f"got {outcome.detail!r}",
                )
                check(
                    "while the capability still reads as present",
                    unreachable.implements("append_day"),
                )
                check(
                    "and nothing was recorded",
                    not os.path.exists(os.path.join(sealed, "store")),
                    "the store was created despite the refusal",
                )
        finally:
            # ⛔ Restored before the directory is removed: a mode the cleanup
            # cannot traverse leaves the temporary tree behind on every run.
            os.chmod(sealed, 0o700)

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(self_test())
