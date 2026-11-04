#!/usr/bin/env python3
"""This host's own decisions about a run, held against a transport that records.

What the contract's suite holds is the contract -- the operation list, the absent
case, a kind of `none`. This holds what the implementation beside it decided, and
every one of those is reachable only by answering as the host does: the read-only
property, the two readings that are withheld rather than invented, the go bound to
its own dispatch, and the two ref forms that are each other's refusal.

⛔ **No call leaves this process.** The transport is replaced by a fake that
answers by **what was asked for** and records every call with whether it writes --
a mock keyed on call order would redden on a refactor and stay green on a call
that moved to the wrong endpoint. ⚠️ A suite that made real calls here would
dispatch a run against whatever this repository configures, which is the one
operation on this port that is not a read.

⚠️ **The port is what every call goes through**, never the module's functions
directly. The adapter resolves no project for itself, so a direct call would
bypass the one place a configuration is bound -- and the suite would be
exercising a path no role takes.

Usage:
    _github_suite.py    hold this host's run operations to their own decisions
"""

from __future__ import annotations

import os
import sys

_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import config  # noqa: E402
import host_checks  # noqa: E402
import port  # noqa: E402
from runs import github as implementation  # noqa: E402

# The port this suite drives. ⚠️ Written out, which a suite may do about the thing
# it is a suite for -- what is read off the surface is the port's section, its
# operation list and its prefix, every one of them through `port.port_spec`.
PORT = "host.runs.kind"

# A commit and a branch, each in the form the operation that takes it requires.
# ⚠️ Fixed rather than read from this repository: a fixture taken from the tree is
# one whose failures depend on where it ran.
A_COMMIT = "0" * 39 + "a"
ANOTHER_COMMIT = "1" * 39 + "b"
A_BRANCH = "release/next"
A_WORKFLOW = "Deploy"
A_RUN = "7001"
A_SUCCESSOR = "7002"


class _Host:
    """A transport that answers as the host does, and records what was asked.

    ⛔ A fake rather than a mock: it answers by the endpoint or subcommand asked
    for, so a refactor that reorders calls does not redden it and a call that
    moves to the wrong endpoint does.

    ⛔ Every call's `writes` is recorded, which is what makes § 28's read-only
    property an assertion rather than a claim: the three reads must never pass it.
    """

    def __init__(self, answers: dict | None = None, *, fail_on: str | None = None):
        self.answers = answers or {}
        self.fail_on = fail_on
        self.calls: list[tuple[str, bool]] = []

    def __call__(self, args, *, parse, timeout, tolerate_exit, writes):
        shown = " ".join(args)
        self.calls.append((shown, writes))
        if self.fail_on and self.fail_on in shown:
            raise port.HostUnavailable(f"`gh {shown}` failed: the host said no")
        for key, answer in self.answers.items():
            if key in shown:
                return answer
        if parse:
            # ⛔ A fake that refuses an unexpected call rather than answering one.
            # A fake answering everything cannot tell a call that moved from a
            # fixture that is thin -- and this suite's assertions are about which
            # calls happen at all.
            raise AssertionError(f"the suite has no answer for `gh {shown}`")
        return ""

    @property
    def writing(self) -> list[str]:
        return [shown for shown, writes in self.calls if writes]

    @property
    def asked(self) -> list[str]:
        return [shown for shown, _writes in self.calls]


def _configuration(more: dict | None = None) -> config.Config:
    """A whole example, with this kind written onto the port it answers for.

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
    for path, value in (more or {}).items():
        node = loaded.data
        parts = path.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return loaded


def _port(host: _Host, more: dict | None = None) -> port.Port:
    implementation.TRANSPORT = host
    return port.Port(_configuration(more), port.port_spec(PORT))


def _run_record(**over) -> dict:
    record = {
        "id": int(A_RUN),
        "name": A_WORKFLOW,
        "head_sha": A_COMMIT,
        "workflow_id": 55,
        "created_at": "2026-03-04T10:00:00Z",
        "conclusion": implementation.PASSED,
        "run_attempt": 1,
    }
    record.update(over)
    return record


def _jobs(*steps: list[dict]) -> dict:
    return {"jobs": [{"steps": list(each)} for each in steps]}


def _step(conclusion: str | None) -> dict:
    return {"conclusion": conclusion}


def _answers(**over) -> dict:
    """An answer for each endpoint a read makes, keyed by what identifies it.

    ⛔ Ordered longest key first where two overlap: the jobs endpoint's path
    contains the run endpoint's, so a shorter key would answer both and the step
    count would come back from the run record.
    """
    answers = {
        f"actions/runs/{A_RUN}/jobs": _jobs([_step(implementation.PASSED)]),
        f"actions/runs/{A_RUN}": _run_record(),
        f"actions/runs?head_sha={A_COMMIT}": {"workflow_runs": [_run_record()]},
        "actions/workflows/55/runs": {"workflow_runs": [_run_record()]},
    }
    answers.update(over)
    return dict(sorted(answers.items(), key=lambda pair: -len(pair[0])))


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
        """The key a call refuses on, or what it did instead.

        ⛔ Every exception and not only `ConfigError`: a guard removed while
        planting leaves the next line raising something else, and a traceback out
        of here would end the report before the assertion that exists for it.
        """
        try:
            call()
        except config.ConfigError as error:
            return error.key
        except Exception as error:  # noqa: BLE001 -- see the docstring
            return f"<raised {type(error).__name__}: {error}>"
        return None

    def message(call) -> str:
        try:
            call()
        except Exception as error:  # noqa: BLE001 -- a message, whatever it was
            return str(error)
        return ""

    was = implementation.TRANSPORT
    try:
        spec = port.port_spec(PORT)
        operations = f"{spec.prefix}.operations"

        # Every operation § 28 states is implemented, asserted as a **relation**
        # against the surface's own list rather than as a count or a list of
        # names: a number here would be wrong the next time the section grows.
        host = _Host(_answers())
        here = _port(host)
        check(
            "this host implements every operation the surface states",
            all(here.implements(operation) for operation in here.stated),
            f"absent: {sorted(o for o in here.stated if not here.implements(o))!r}",
        )

        # --- the runs a commit has -----------------------------------------

        listed = here.invoke("runs_for_ref", A_COMMIT)
        check("a commit's runs are listed", listed.performed, str(listed))
        check(
            "and each is named by its workflow, which is what `host.checks` is keyed on",
            listed.result["runs"] == [{
                "workflow": A_WORKFLOW,
                "run": int(A_RUN),
                "attempt": 1,
                "created_at": "2026-03-04T10:00:00Z",
            }],
            f"listed {listed.result!r}",
        )
        # ⛔ A branch is refused and an abbreviated commit is too. Both would be
        # accepted by the host's own filter and come back empty, which reads
        # exactly like a commit it made no run for -- precondition 2 answered
        # wrongly rather than unanswered.
        for given in (A_BRANCH, A_COMMIT[:7], "", "HEAD"):
            check(
                f"a listing keyed on {given!r} is refused, naming the operation",
                refused(lambda value=given: here.invoke("runs_for_ref", value))
                == f"{operations}.runs_for_ref",
                f"reported {refused(lambda value=given: here.invoke('runs_for_ref', value))!r}",
            )
        # An empty listing is an answer: the capability is present, and what it
        # means is the caller's reading.
        empty = _Host(_answers(**{f"actions/runs?head_sha={A_COMMIT}": {"workflow_runs": []}}))
        quiet = _port(empty).invoke("runs_for_ref", A_COMMIT)
        check(
            "a commit with no run comes back as an empty list, not a failure",
            quiet.performed and quiet.result["runs"] == [],
            f"got {str(quiet)!r}",
        )
        # ⛔ And a body with no run list in it is **unestablished**, never empty.
        # The two are one key apart and read identically if they are not held
        # apart: a host that answered something else about this commit would
        # otherwise report precondition 2 unmet.
        shapeless = _Host(_answers(**{f"actions/runs?head_sha={A_COMMIT}": {"total": 0}}))
        broken = _port(shapeless).invoke("runs_for_ref", A_COMMIT)
        check(
            "a listing with no run list in it is a failed call and not an empty answer",
            broken.failed and not broken.performed,
            f"got {str(broken)!r}",
        )

        # --- how one concluded ---------------------------------------------

        host = _Host(_answers())
        here = _port(host)
        read = here.invoke("conclusion", A_RUN)
        check(
            "a run that executed a step and passed reads as green",
            read.performed and read.result["reading"] == host_checks.GREEN,
            f"read {read.result!r}",
        )
        # ⛔ The host's own conclusion word does not reach the caller. One word
        # arrives on two of the four readings, so a caller handed it would have to
        # make the distinction this port exists to make once.
        check(
            "and the host's conclusion word is nowhere in the answer",
            implementation.PASSED not in str(read.result),
            f"read {read.result!r}",
        )
        failed = _port(_Host(_answers(**{
            f"actions/runs/{A_RUN}": _run_record(conclusion="failure"),
        }))).invoke("conclusion", A_RUN)
        check(
            "a run that executed a step and did not pass reads as failed",
            failed.result["reading"] == host_checks.FAILED,
            f"read {failed.result!r}",
        )
        # ⛔ Zero **executed** steps, with a step list the host did state: skipped
        # steps ran nothing, so this is the never-started reading rather than a
        # count the host withheld.
        skipped = _port(_Host(_answers(**{
            f"actions/runs/{A_RUN}/jobs": _jobs([_step(implementation.SKIPPED), _step(None)]),
            f"actions/runs/{A_RUN}": _run_record(conclusion="cancelled"),
        }))).invoke("conclusion", A_RUN)
        check(
            "a run whose every step was skipped reads as never started",
            skipped.result["reading"] == host_checks.NEVER_STARTED,
            f"read {skipped.result!r}",
        )
        # ⛔ And the two shapes that are **unavailable** rather than zero, each
        # withholding the reading and naming precondition 3. Read as zero, each
        # would report the queue about a run that may have executed everything it
        # has -- the measured defect this arm exists for.
        for label, jobs in (
            ("no job list", {"jobs": []}),
            ("a job with no step list", _jobs([])),
        ):
            withheld = _port(_Host(_answers(**{
                f"actions/runs/{A_RUN}/jobs": jobs,
            }))).invoke("conclusion", A_RUN)
            check(
                f"{label} withholds the reading and names precondition 3",
                withheld.result["reading"] is None
                and "precondition 3" in withheld.result["unanswered"],
                f"read {withheld.result!r}",
            )
            check(
                f"and {label} is never read as the never-started reading",
                withheld.result["reading"] != host_checks.NEVER_STARTED,
                f"read {withheld.result!r}",
            )

        # A run the host has not concluded: precondition 4, and no watch unasked.
        unconcluded = _Host(_answers(**{
            f"actions/runs/{A_RUN}": _run_record(conclusion=None),
        }))
        waiting = _port(unconcluded).invoke("conclusion", A_RUN)
        check(
            "an unconcluded run withholds the reading and names precondition 4",
            waiting.result["reading"] is None
            and "precondition 4" in waiting.result["unanswered"],
            f"read {waiting.result!r}",
        )
        check(
            "and nothing was watched, the caller not having asked to wait",
            not any("run watch" in asked for asked in unconcluded.asked),
            f"asked {unconcluded.asked!r}",
        )
        # ⛔ Asked to wait, the host's own blocking client is what runs -- never a
        # sleep and never a poll (§ 2). ⚠️ And its exit status is not read: the
        # client exits non-zero for a run that failed, which is an answer.
        watched = _Host(_answers(**{
            f"actions/runs/{A_RUN}": _run_record(conclusion="failure"),
        }))
        waited = _port(watched).invoke("conclusion", A_RUN, "yes")
        check(
            "asked to wait, the host's own watch is what blocks",
            any("run watch" in asked for asked in watched.asked),
            f"asked {watched.asked!r}",
        )
        check(
            "and the watch happens before the run is read",
            next(i for i, a in enumerate(watched.asked) if "run watch" in a)
            < next(i for i, a in enumerate(watched.asked) if "actions/runs/" in a),
            f"asked {watched.asked!r}",
        )
        check(
            "and a run that failed is still an answer rather than a failed call",
            waited.performed and waited.result["reading"] == host_checks.FAILED,
            f"got {str(waited)!r}",
        )
        check(
            "a conclusion asked for no run at all is refused, naming the operation",
            refused(lambda: here.invoke("conclusion", "  ")) == f"{operations}.conclusion",
        )

        # --- supersession, read only where a group is stated ----------------

        # ⚠️ No `host.runner` at all: § 2 states that as no run of this project's
        # retiring another, so nothing is looked up. ⛔ Asserted on the **call**
        # and not only on the reading: a lookup made and discarded would be this
        # module asking a question the project already answered.
        no_group = _Host(_answers(**{
            f"actions/runs/{A_RUN}": _run_record(conclusion="cancelled"),
            f"actions/runs/{A_RUN}/jobs": _jobs([_step(implementation.PASSED)]),
        }))
        _port(no_group, {"host.runner": None}).invoke("conclusion", A_RUN)
        check(
            "with no supersession group stated, no successor is looked up",
            not any("actions/workflows/" in asked for asked in no_group.asked),
            f"asked {no_group.asked!r}",
        )
        # Stated, a newer run of the same workflow for the same commit is the
        # successor, and the reading sends the reader to it.
        grouped = {
            "host.runner": {
                "label": "<a label>",
                "concurrent_jobs": 1,
                "budget_minutes": 30,
                "supersedes": "<a group>",
            }
        }
        superseded = _port(
            _Host(_answers(**{
                f"actions/runs/{A_RUN}": _run_record(conclusion="cancelled"),
                "actions/workflows/55/runs": {"workflow_runs": [
                    _run_record(),
                    _run_record(id=int(A_SUCCESSOR), created_at="2026-03-04T11:00:00Z"),
                ]},
            })),
            grouped,
        ).invoke("conclusion", A_RUN)
        check(
            "with a group stated, a newer run for the same commit is the successor",
            superseded.result["reading"] == host_checks.SUPERSEDED
            and superseded.result["read_instead"] == A_SUCCESSOR,
            f"read {superseded.result!r}",
        )
        # And an older run is not a successor: the comparison is on when, not on
        # there being another run at all.
        older = _port(
            _Host(_answers(**{
                f"actions/runs/{A_RUN}": _run_record(conclusion="failure"),
                "actions/workflows/55/runs": {"workflow_runs": [
                    _run_record(id=6000, created_at="2026-03-04T09:00:00Z"),
                ]},
            })),
            grouped,
        ).invoke("conclusion", A_RUN)
        check(
            "while an older run for the same commit is not one",
            older.result["reading"] == host_checks.FAILED,
            f"read {older.result!r}",
        )

        # --- the log --------------------------------------------------------

        printed = "\n".join(f"line {number}" for number in range(1, 11))
        logged = _port(_Host({"run view": printed})).invoke("log", A_RUN, 3)
        check(
            "a log comes back as its tail",
            logged.result["text"] == "line 8\nline 9\nline 10",
            f"read {logged.result!r}",
        )
        # ⛔ Both counts, because a cut log that did not say so reads as the whole
        # of what the run printed -- and what a reader does with a log is conclude
        # from what is not in it.
        check(
            "with how many lines came back and how many there were",
            logged.result["lines"] == 3 and logged.result["of"] == 10,
            f"read {logged.result!r}",
        )
        whole = _port(_Host({"run view": printed})).invoke("log", A_RUN)
        check(
            "a log shorter than the tail asked for comes back whole, counts agreeing",
            whole.result["lines"] == 10 and whole.result["of"] == 10,
            f"read {whole.result!r}",
        )
        for given in (0, -1, "some"):
            check(
                f"a log of {given!r} lines is refused, naming the operation",
                refused(lambda value=given: here.invoke("log", A_RUN, value))
                == f"{operations}.log",
            )
        check(
            "a log asked for no run at all is refused, naming the operation",
            refused(lambda: here.invoke("log", "")) == f"{operations}.log",
        )

        # --- the read-only property ----------------------------------------
        #
        # ⛔ Asserted as a relation over every read this suite made: § 28 states
        # the property and this is where it can fail. A call that started writing
        # would redden here rather than in whatever it wrote.
        reading_only = _Host(_answers(**{"run view": printed}))
        only = _port(reading_only)
        only.invoke("runs_for_ref", A_COMMIT)
        only.invoke("conclusion", A_RUN)
        only.invoke("log", A_RUN)
        check(
            "the listing, the conclusion and the log make no call that writes",
            reading_only.writing == [],
            f"wrote with {reading_only.writing!r}",
        )
        check(
            "and they did make calls, so the assertion above is about something",
            len(reading_only.asked) >= 3,
            f"asked {reading_only.asked!r}",
        )

        # --- the dispatch and its go ---------------------------------------

        a_go = f"approved: run {A_WORKFLOW} against {A_BRANCH} with env=staging"
        sent = _Host({"workflow run": ""})
        started = _port(sent).invoke(
            "dispatch", A_WORKFLOW, A_BRANCH, a_go, "env=staging"
        )
        check("a dispatch with a go that names it goes through", started.performed, str(started))
        check(
            "and it is the one call on this port that writes",
            sent.writing == sent.asked and len(sent.writing) == 1,
            f"asked {sent.calls!r}",
        )
        check(
            "the workflow, the ref and each typed input reach the host",
            all(
                token in sent.asked[0]
                for token in (A_WORKFLOW, A_BRANCH, "--field", "env=staging")
            ),
            f"asked {sent.asked!r}",
        )
        # ⛔ No run id is invented. The client prints none for a dispatch, and a
        # report naming a run nobody can read is worse than one naming none.
        check(
            "and the answer names how to find the run rather than inventing its id",
            started.result["find_it_with"] == "runs_for_ref"
            and "run" not in started.result,
            f"answered {started.result!r}",
        )

        # ⛔ Every refusal below happens **before** the write. A rail that refused
        # after dispatching would be a rail that reported a refusal and started a
        # run, which is the one outcome worse than no rail at all.
        for label, call in (
            ("no go at all", lambda h: (A_WORKFLOW, A_BRANCH, "")),
            ("a go naming another ref", lambda h: (
                A_WORKFLOW, A_BRANCH, f"approved: {A_WORKFLOW} against release/last-week"
            )),
            ("a go naming another workflow", lambda h: (
                A_WORKFLOW, A_BRANCH, f"approved: Something Else against {A_BRANCH}"
            )),
            ("a go that does not name an input's value", lambda h: (
                A_WORKFLOW, A_BRANCH, f"approved: {A_WORKFLOW} against {A_BRANCH}",
                "env=production",
            )),
            ("a commit where a branch belongs", lambda h: (
                A_WORKFLOW, A_COMMIT, f"approved: {A_WORKFLOW} against {A_COMMIT}"
            )),
            ("an input that is not `name=value`", lambda h: (
                A_WORKFLOW, A_BRANCH, f"approved: {A_WORKFLOW} against {A_BRANCH}", "production"
            )),
            ("no workflow at all", lambda h: ("", A_BRANCH, "approved")),
        ):
            attempted = _Host({"workflow run": ""})
            at = _port(attempted)
            reported = refused(lambda p=at, h=attempted: p.invoke("dispatch", *call(h)))
            check(
                f"a dispatch with {label} is refused, naming the operation",
                reported == f"{operations}.dispatch",
                f"reported {reported!r}",
            )
            check(
                f"and {label} starts nothing",
                attempted.calls == [],
                f"asked {attempted.calls!r}",
            )
        # ⚠️ The refusal does not compose the sentence that would satisfy it: a
        # refusal handing back the string to repeat is a form to fill in rather
        # than an approval to have obtained.
        said = message(lambda: _port(_Host({"workflow run": ""})).invoke(
            "dispatch", A_WORKFLOW, A_BRANCH, f"approved: {A_WORKFLOW} against release/old"
        ))
        check(
            "and the refusal names what was missing rather than the go to pass",
            "the ref" in said and A_BRANCH not in said,
            f"said {said!r}",
        )
        # An input with an empty value is not a token a go can name, so it is not
        # held to naming one -- the one arm of the go check that is about the
        # *absence* of a value rather than a mismatch.
        empty_value = _Host({"workflow run": ""})
        with_blank = _port(empty_value).invoke(
            "dispatch", A_WORKFLOW, A_BRANCH,
            f"approved: {A_WORKFLOW} against {A_BRANCH}", "note=",
        )
        check(
            "an input stated with an empty value does not need naming in the go",
            with_blank.performed and with_blank.result["inputs"] == {"note": ""},
            f"got {str(with_blank)!r}",
        )

        # --- the host that does not answer ---------------------------------
        #
        # ⛔ A failed call and never the stated fallback: the capability is there
        # and the call did not go through, which § 3 holds apart from an absence
        # because a role that took the fallback would be acting on a decision
        # nobody made.
        unreachable = _port(_Host(_answers(), fail_on="actions/runs?head_sha"))
        outcome = unreachable.invoke("runs_for_ref", ANOTHER_COMMIT.replace("b", "a"))
        check(
            "a host that does not answer comes back as a failed outcome",
            outcome.failed and not outcome.performed,
            f"got {str(outcome)!r}",
        )
        check(
            "with the host's own words rather than the surface's fallback",
            "the host said no" in outcome.detail
            and outcome.detail != unreachable.fallback("runs_for_ref"),
            f"got {outcome.detail!r}",
        )
        check(
            "while the capability still reads as present",
            unreachable.implements("runs_for_ref"),
        )

        # The repository's shape, which nothing else checks.
        check(
            "a repository that is not `owner/name` is refused, naming the key",
            refused(
                lambda: _port(_Host(_answers()), {"host.repo": "not-a-pair"})
                .invoke("conclusion", A_RUN)
            )
            == "host.repo",
        )
        # ⛔ And a direct call bypassing the port is refused rather than reading a
        # configuration from wherever the process stands.
        implementation._bound = None
        check(
            "an operation called with no configuration bound is refused, naming the port",
            refused(lambda: implementation.runs_for_ref(A_COMMIT)) == PORT,
        )
    finally:
        implementation.TRANSPORT = was

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(self_test())
