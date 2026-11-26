#!/usr/bin/env python3
"""A deploy target's command run in the background, followed, and read once it ends.

`background` (§ 33 → A run put in the background, and what is handed over while it
runs) is a block on a `command` target, and this module is its one consumer.
⛔ **The order of the run is the surface's**, stated there in a table; what is
here performs it, so a role cannot wait before the log is handed over or read an
outcome while the run is still in flight.

What it owns is the part a role should not perform by eye:

  * **The start**, detached from the session, with the command's output written
    to the log the target states and the status it exits with written to a file
    of its own. ⛔ The command is run whole, as the reader resolved it, and nothing
    is prefixed to it or read out of it.
  * **The record**, written to the artifact store before anything waits, so a
    session that ends first leaves a report of the run in flight.
  * **The reading**, three-valued and never two: a run is `running`, `ended` with
    the status it exited with, or `lost` — its process gone and no status written,
    which is neither delivered nor failed (§ 11).

Usage:
    deploy_run.py [--skills-root DIR] start --target NAME [--choose NAME=VALUE ...]
    deploy_run.py [--skills-root DIR] wait --target NAME --up-to SECONDS
    deploy_run.py [--skills-root DIR] status [--target NAME]
    deploy_run.py --self-test

Exit status: 0 the answer was produced, 1 the start was refused (a run of this
target is still in flight), 2 the configuration could not answer, 3 this target
states no background run, 4 no run of this target is recorded, 5 the wait reached
its bound with the run still running. ⚠️ The last is its own value because a run
still running collapsed into 0 reads as a run that ended.
"""

from __future__ import annotations

import argparse
import datetime
import json
import os
import shlex
import subprocess
import sys
import tempfile
import time

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface

REFUSED = 1
UNREADABLE = 2
NO_BACKGROUND = 3
NO_RECORD = 4
STILL_RUNNING = 5

RECORD = "deploy-run-{target}.json"
RECORD_PREFIX = "deploy-run-"

# How often a wait reads the record. ⚠️ Not a poll of a host: the run is a local
# process this module started, its status lands in a file, and reading that file
# is the only way a process that did not start it can learn it ended.
READ_EVERY = 1.0


def _slug(target: str) -> str:
    """A target's name as a file name; the record carries the name itself."""
    return "".join(ch if ch.isalnum() or ch in "-_" else "-" for ch in target)


def _store(configuration) -> str:
    """The store § 11 names, or the temporary directory where none is carried."""
    where = configuration.get("context.artifacts.dir") or tempfile.gettempdir()
    return os.path.expandvars(where)


def _record_path(store: str, target: str) -> str:
    return os.path.join(store, RECORD.format(target=_slug(target)))


def _held(path: str) -> dict | None:
    """A record on disk, or `None` where there is none or it does not parse."""
    try:
        with open(path, encoding="utf-8") as handle:
            held = json.load(handle)
    except (OSError, ValueError):
        return None
    return held if isinstance(held, dict) else None


def _keep(path: str, record: dict) -> None:
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(record, handle, indent=2, ensure_ascii=False)


def _alive(pid) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    # ⚠️ A child of this very process that has exited stays a zombie until it is
    # reaped, and a signal to a zombie succeeds; reap it without blocking.
    try:
        done, _ = os.waitpid(pid, os.WNOHANG)
    except ChildProcessError:
        return True
    return done == 0


def _ours(record: dict) -> bool:
    """Whether the live process at the record's number is this run's wrapper.

    ⛔ A number is reused — after a reboot, or once the counter wraps — so a live
    process at it is not evidence the run is still going: read as running, a run
    that ended long ago would hold every advance and refuse every later start for
    good. The wrapper carries the status file as an argument, so its command line
    names it. ⚠️ Where the command line cannot be read at all the number is
    believed, since reading a run as ended is the direction that advances.
    """
    try:
        done = subprocess.run(
            ["ps", "-p", str(record.get("pid")), "-o", "args="],
            capture_output=True, text=True, check=False,
        )
    except OSError:
        return True
    if done.returncode != 0 or not done.stdout.strip():
        return True
    return (record.get("status_file") or "\0") in done.stdout


def follow_command(log: str) -> str:
    """The command a person runs to follow the log while the run is in flight."""
    return f"tail -f {shlex.quote(log)}"


def _status_of(record: dict) -> int | None:
    """The status the run's wrapper wrote, or `None` where none is written yet."""
    try:
        with open(record.get("status_file") or "", encoding="utf-8") as handle:
            text = handle.read().strip()
    except OSError:
        return None
    try:
        return int(text)
    except ValueError:
        return None


def _settle(pid: int, status_file: str, up_to: float = 5.0) -> None:
    """Return once the wrapper has replaced the forked copy of this process.

    ⛔ Between the fork and the exec the child's command line is this module's,
    so a reading taken in that window would find a live process that is not the
    run's wrapper and call the run lost. The record is written after this.
    """
    deadline = time.monotonic() + up_to
    record = {"pid": pid, "status_file": status_file}
    while time.monotonic() < deadline:
        if _status_of(record) is not None or not _alive(pid):
            return
        try:
            done = subprocess.run(["ps", "-p", str(pid), "-o", "args="],
                                  capture_output=True, text=True, check=False)
        except OSError:
            return
        if done.returncode != 0 or status_file in done.stdout:
            return
        time.sleep(0.02)


def reading(record: dict) -> dict:
    """What a record says about its run now: running, ended, or lost.

    ⛔ The status file is read first: a run whose status is written has ended,
    whatever its process looks like. Only then is the process asked about, and a
    process gone with no status written is `lost` rather than either outcome.
    """
    status = _status_of(record)
    if status is not None:
        return {"state": "ended", "status": status, "advance_held": False}
    started_on = record.get("host")
    if started_on and started_on != os.uname().nodename:
        # ⛔ A process number means nothing on another machine, and one that
        # happens to be alive here would read a finished run as running.
        return {
            "state": "lost",
            "status": None,
            "advance_held": True,
            "why": f"the run was started on {started_on}, and its process can be read "
            "only there (§ 33)",
        }
    if _alive(record.get("pid")) and _ours(record):
        return {"state": "running", "status": None, "advance_held": True}
    # ⛔ Read once more: a run that wrote its status and exited between the
    # first read and the process check is ended, not lost.
    status = _status_of(record)
    if status is not None:
        return {"state": "ended", "status": status, "advance_held": False}
    return {
        "state": "lost",
        "status": None,
        "advance_held": True,
        "why": "the run's process is gone and no status was written, so how it "
        "ended could not be established; its log is a person's to read (§ 11)",
    }


def start(target: dict, store: str) -> tuple[int, dict]:
    """Rows 1 and 2 of § 33's order: start detached, record, hand the log over.

    `target` is the reader's resolution of one entry (`Config.deploy_target`).
    """
    background = target.get("background")
    if not background:
        return NO_BACKGROUND, {
            "target": target.get("target"),
            "background": None,
            "why": "this target states no background run, so its command is invoked "
            "in the foreground as before (§ 33)",
        }
    path = _record_path(store, target["target"])
    held = _held(path)
    if held is not None:
        now = reading(held)
        if now["state"] == "running":
            return REFUSED, {
                "target": target["target"],
                "started": False,
                "why": "a run of this target is still in flight; it is read, not "
                "started again (§ 33)",
                "record": path,
                **{key: held.get(key) for key in ("pid", "log", "started_at")},
                "follow": follow_command(held.get("log") or ""),
            }
    runs_at = target["runs_at"]
    log = os.path.join(runs_at, os.path.expandvars(background["log"]))
    log = os.path.normpath(log)
    status_file = path[: -len(".json")] + ".status"
    for stale in (status_file,):
        try:
            os.remove(stale)
        except FileNotFoundError:
            pass
    os.makedirs(os.path.dirname(log) or ".", exist_ok=True)
    os.makedirs(store, exist_ok=True)
    # ⛔ The command runs in a shell of its own, so an `exit` inside it ends that
    # shell and never the one writing the status after it.
    wrapper = 'sh -c "$1"; printf "%s\\n" "$?" > "$2"'
    with open(log, "w", encoding="utf-8") as output:
        process = subprocess.Popen(
            ["sh", "-c", wrapper, "sh", target["command"], status_file],
            cwd=runs_at,
            stdin=subprocess.DEVNULL,
            stdout=output,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    _settle(process.pid, status_file)
    record = {
        "target": target["target"],
        "command": target["command"],
        "runs_at": runs_at,
        "log": log,
        "status_file": status_file,
        "pid": process.pid,
        "started_at": datetime.datetime.now(datetime.timezone.utc).isoformat(
            timespec="seconds"
        ),
        "host": os.uname().nodename,
    }
    _keep(path, record)
    return 0, {
        "target": target["target"],
        "started": True,
        "record": path,
        "log": log,
        "follow": follow_command(log),
        "pid": process.pid,
        "started_at": record["started_at"],
        "next": "hand the log and the follow command to the person, then wait; "
        "nothing advances until the run has ended (§ 33)",
    }


def wait(target_name: str, store: str, up_to: float) -> tuple[int, dict]:
    """Rows 3 and 4: read the record until the run ends, for `up_to` seconds."""
    path = _record_path(store, target_name)
    held = _held(path)
    if held is None:
        return NO_RECORD, {
            "target": target_name,
            "record": path,
            "why": "no run of this target is recorded in the store",
        }
    deadline = time.monotonic() + max(up_to, 0.0)
    now = reading(held)
    while now["state"] == "running" and time.monotonic() < deadline:
        time.sleep(min(READ_EVERY, max(deadline - time.monotonic(), 0.0)))
        now = reading(held)
    answer = {"target": target_name, "record": path, "log": held.get("log"),
              "follow": follow_command(held.get("log") or ""),
              "started_at": held.get("started_at"), **now}
    if now["state"] == "running":
        return STILL_RUNNING, answer
    return 0, answer


def status(store: str, target_name: str | None = None) -> tuple[int, dict]:
    """Every record in the store, or one target's, read without waiting."""
    if target_name is not None:
        path = _record_path(store, target_name)
        held = _held(path)
        if held is None:
            return NO_RECORD, {"target": target_name, "record": path,
                               "why": "no run of this target is recorded in the store"}
        return 0, {"runs": [{"record": path, **held, **reading(held)}]}
    runs = []
    try:
        names = sorted(os.listdir(store))
    except OSError:
        names = []
    for name in names:
        if name.startswith(RECORD_PREFIX) and name.endswith(".json"):
            path = os.path.join(store, name)
            held = _held(path)
            if held is not None:
                runs.append({"record": path, **held, **reading(held)})
    return 0, {"store": store, "runs": runs}


# --- self-test ---------------------------------------------------------------


def self_test() -> int:
    failures = 0

    def check(label: str, held: bool, saw: object = "") -> None:
        nonlocal failures
        if held:
            print(f"  ok    {label}")
        else:
            failures += 1
            print(f"  FAIL  {label}: {saw}")

    print("The surface states what this module reads:")
    with open(config.SURFACE, encoding="utf-8") as handle:
        facts = config.surface_facts(handle.read())
    declared = sorted(
        path[len("deploy.background."):]
        for path in facts["declared"]
        if path.startswith("deploy.background.")
    )
    check("§ 33 declares the background run's one key, `log`", declared == ["log"], declared)

    scratch = tempfile.mkdtemp(prefix="deploy-run-test-")
    store = os.path.join(scratch, "store")
    tree = os.path.join(scratch, "tree")
    os.makedirs(tree)

    def target(command: str, name: str = "a-target", log: str | None = "out/deploy.log"):
        return {
            "target": name,
            "command": command,
            "runs_at": tree,
            "background": None if log is None else {"log": log},
        }

    try:
        print("\nA target stating no background run:")
        code, got = start(target("true", log=None), store)
        check("is refused with its own exit and runs nothing", code == NO_BACKGROUND
              and got["background"] is None, (code, got))
        check("and leaves no record behind",
              not os.path.exists(_record_path(store, "a-target")), os.listdir(scratch))

        print("\nThe start, and the hand-over before any wait:")
        gate = os.path.join(scratch, "gate")
        code, got = start(
            target(f"echo begun; while [ ! -e {shlex.quote(gate)} ]; do sleep 0.1; done; "
                   "echo finished; exit 7"),
            store,
        )
        check("a background target starts and returns at once", code == 0
              and got["started"] is True, (code, got))
        log = os.path.join(tree, "out", "deploy.log")
        check("the log is where the target states, relative to where the command runs",
              got.get("log") == log, got.get("log"))
        check("the hand-over names a command following that log",
              got.get("follow") == follow_command(log), got.get("follow"))
        record = _held(_record_path(store, "a-target"))
        check(
            "a record is written before anything waits, naming the run in flight",
            isinstance(record, dict)
            and all(record.get(key) for key in
                    ("target", "command", "runs_at", "log", "pid", "started_at")),
            record,
        )
        code, now = status(store)
        check("the record reads as running while the run is in flight",
              code == 0 and [run["state"] for run in now["runs"]] == ["running"], now)
        check("and holds the advance while it runs",
              now["runs"] and now["runs"][0]["advance_held"] is True, now)

        code, again = start(target("echo second"), store)
        check("a second start while the first is in flight is refused",
              code == REFUSED and again["started"] is False, (code, again))
        check("and the first run's record is left as it was",
              _held(_record_path(store, "a-target")) == record,
              _held(_record_path(store, "a-target")))

        print("\nThe wait, bounded, and nothing read before the run ends:")
        code, got = wait("a-target", store, 0.3)
        check("a wait reaching its bound reports the run still running, with its own exit",
              code == STILL_RUNNING and got["state"] == "running"
              and got["status"] is None and got["advance_held"] is True, (code, got))
        open(gate, "w").close()
        code, got = wait("a-target", store, 10)
        check("once the run ends, the wait reads the status it exited with",
              code == 0 and got["state"] == "ended" and got["status"] == 7, (code, got))
        check("and the advance is no longer held by the run",
              got.get("advance_held") is False, got)
        with open(log, encoding="utf-8") as handle:
            written = handle.read()
        check("the command's output reached the log",
              "begun" in written and "finished" in written, written)

        print("\nA run that ended, a run that is lost, and a run not recorded:")
        code, got = start(target("exit 0"), store)
        check("an ended run's target may be started again", code == 0, (code, got))
        code, got = wait("a-target", store, 10)
        check("an `exit` inside the command does not stop the status being written",
              code == 0 and got["status"] == 0, (code, got))
        readings = []
        for _ in range(30):
            start(target("exit 0", name="quick"), store)
            readings.append(reading(_held(_record_path(store, "quick")))["state"])
            wait("quick", store, 10)
        check("a run read the moment it starts is running or ended, never lost",
              "lost" not in readings, readings)
        os.remove(_record_path(store, "quick"))
        lost = {
            "target": "gone",
            "pid": 2 ** 22 + 12345,
            "status_file": os.path.join(scratch, "never-written.status"),
            "log": os.path.join(scratch, "gone.log"),
        }
        _keep(_record_path(store, "gone"), lost)
        code, got = wait("gone", store, 0.2)
        check("a process gone with no status written is lost, never ended",
              code == 0 and got["state"] == "lost" and got["status"] is None, (code, got))
        check("and a lost run holds the advance as a running one does",
              got.get("advance_held") is True, got)
        elsewhere = dict(_held(_record_path(store, "a-target")), host="another-machine")
        elsewhere.pop("status_file")
        elsewhere["pid"] = os.getpid()
        check("a record started on another machine reads lost, even where its number is alive",
              reading(elsewhere)["state"] == "lost", reading(elsewhere))
        reused = dict(lost, pid=os.getpid(), host=os.uname().nodename)
        check("a live process at a reused number that is not this run's wrapper reads lost",
              reading(reused)["state"] == "lost", reading(reused))
        code, got = wait("never-started", store, 0.1)
        check("a target with no recorded run says so with its own exit",
              code == NO_RECORD, (code, got))
        code, got = status(store, "never-started")
        check("and so does a status asked about it", code == NO_RECORD, (code, got))
        code, got = status(store)
        check("a status without a target lists every recorded run in the store",
              sorted(run["target"] for run in got["runs"]) == ["a-target", "gone"], got)
    finally:
        subprocess.run(["rm", "-rf", scratch], check=False)

    print(f"\n{'all held' if not failures else f'{failures} failed'}")
    return 1 if failures else 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--skills-root", default=None)
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="act")
    started = sub.add_parser("start", help="start the target's command in the background")
    started.add_argument("--target", required=True)
    started.add_argument("--choose", action="append", default=[], metavar="NAME=VALUE")
    waited = sub.add_parser("wait", help="read the run until it ends, up to a bound")
    waited.add_argument("--target", required=True)
    waited.add_argument("--up-to", type=float, required=True, metavar="SECONDS")
    read = sub.add_parser("status", help="every recorded run, or one target's")
    read.add_argument("--target", default=None)
    args = parser.parse_args(argv)

    if args.self_test:
        return self_test()
    if args.act is None:
        parser.error("name an act: start, wait or status")
    try:
        configuration = config.load(args.skills_root or os.getcwd())
        store = _store(configuration)
        if args.act == "start":
            resolved = configuration.deploy_target(args.target, args.choose)
            if resolved.get("reached_by") != "command":
                code, answer = NO_BACKGROUND, {
                    "target": args.target,
                    "why": f"the target is reached by `{resolved.get('reached_by')}`, "
                    "which runs no local command (§ 33)",
                }
            elif resolved.get("reachable") is False:
                code, answer = UNREADABLE, {
                    "target": args.target,
                    "why": f"the directory the command runs in, {resolved.get('runs_at')}, "
                    "is not there (§ 1)",
                }
            else:
                code, answer = start(resolved, store)
        elif args.act == "wait":
            code, answer = wait(args.target, store, args.up_to)
        else:
            code, answer = status(store, args.target)
    except config.ConfigError as error:
        print(json.dumps({"error": str(error)}, indent=2, ensure_ascii=False))
        return UNREADABLE
    print(json.dumps(answer, indent=2, ensure_ascii=False))
    return code


if __name__ == "__main__":
    sys.exit(main())
