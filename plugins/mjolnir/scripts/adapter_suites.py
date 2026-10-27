#!/usr/bin/env python3
"""Run every installed implementation's own suite, whatever is installed.

The port's contract has a suite of its own and the gate runs it; what it holds is
the **contract** -- the operation list, the absent case, the writer refusal. An
implementation's own decisions are not reachable from there: a cursor followed to
the end, an id resolved by name, a guard that refuses before it writes. Those live
in the implementation and are held by a suite beside them.

⛔ **This runner names no tracker, no store and no port.** A port's own package is
the one place in the toolkit the thing behind it may be named, and a gate entry
per implementation would spell one in the configuration and again in a workflow
file. So the gate runs *this*, which asks the surface which ports there are, asks
each port what is installed, and runs whatever suite each module exposes -- a new
implementation, and a new port, are covered the moment they land, with nothing to
remember.

⚠️ **An implementation with no suite is reported, not failed.** The first one
built was proved against the live tracker this repository runs on, and a runner
that reddened for it would be refusing a decision somebody made. What *is* a
failure is finding no implementation at all: that is a runner holding nothing
while reporting green, which is the one shape every check here is written against.

⛔ **There is no `--self-test`, deliberately.** The sibling scripts carry one
because their job is something else and the suite is a mode; this script's job
*is* running suites, and its own holding is the count below.

Usage:
    adapter_suites.py             run every installed implementation's suite
"""

from __future__ import annotations

import os
import sys

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import port  # noqa: E402
from config import ConfigError  # noqa: E402


def installed_suites() -> dict[tuple[str, str], object]:
    """`(port name, kind) -> the suite that module exposes, or None`.

    Read from the modules discovery imported rather than from a list: the port
    already knows what is installed, and a second list here is the shape § 3
    forbids -- one allowed to disagree with what is actually built.

    ⛔ Keyed by the port as well as the kind. Two ports may state the same kind
    word -- nothing on the surface stops them -- and a dictionary keyed on the
    kind alone would run one of their suites and silently drop the other, while
    the count read one.
    """
    suites: dict[tuple[str, str], object] = {}
    for name, spec in sorted(port.surface_ports().items()):
        port.load_adapters(spec)
        for module_name, module in list(sys.modules.items()):
            if not module_name.startswith(f"{spec.package}."):
                continue
            # ⛔ The package's own rule, read here rather than restated: a module
            # whose name opens with `_` is not an implementation, which is why
            # discovery skips it. ⚠️ Without this a suite living in a module of
            # its own counts as a second implementation of its own kind -- it
            # imports the names it exercises, `KIND` among them -- and its suite
            # would be run twice while the count read one too many.
            if module_name.rpartition(".")[2].startswith("_"):
                continue
            kind = getattr(module, "KIND", None)
            if kind:
                suites[(name, kind)] = getattr(module, "self_test", None)
    return suites


def main(argv: list[str]) -> int:
    if argv:
        print(__doc__.strip().splitlines()[-1], file=sys.stderr)
        return 2
    try:
        suites = installed_suites()
    except ConfigError as error:
        # ⛔ A verdict rather than a traceback: a module that is present and
        # broken is this toolkit's own mistake, and the gate running this has to
        # report it as a red line.
        print(f"  FAIL  an implementation could not be installed: {error}")
        print("\n1 implementation did not load.")
        return 1

    if not suites:
        print("  FAIL  no implementation of any port is installed, so this run holds nothing")
        print("\n1 assertion did not hold.")
        return 1

    # ⛔ Every port is represented, asserted rather than assumed. A port whose
    # package holds nothing leaves this runner covering the other one and
    # reporting green -- which is a whole port's implementations held by nothing
    # while the count below looks healthy.
    failed, without, missing = [], [], []
    for name in sorted(port.surface_ports()):
        if not any(at == name for at, _kind in suites):
            missing.append(name)

    for at, kind in sorted(suites):
        suite = suites[(at, kind)]
        if suite is None:
            without.append(f"{at} / {kind}")
            continue
        label = f"{at} / {kind}"
        print(f"\n--- the `{label}` implementation " + "-" * max(0, 40 - len(label)))
        if suite() != 0:
            failed.append(label)

    print()
    print(f"{len(suites)} implementation(s) installed, {len(suites) - len(without)} with a suite.")
    for label in without:
        print(
            f"  no suite: `{label}` -- reported rather than failed, which is a "
            "decision somebody made and not an absence this runner can judge."
        )
    for name in missing:
        print(f"  FAIL  no implementation is installed for the `{name}` port")
    if failed or missing:
        shortfall = failed + [f"nothing installed for {name}" for name in missing]
        print(f"\n{len(shortfall)} implementation(s) did not hold: {', '.join(shortfall)}.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
