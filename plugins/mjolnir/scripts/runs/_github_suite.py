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

# The example every fixture is built over, ⛔ named rather than taken by position:
# what several arms below assert turns on this example stating no `host.runner`,
# which a filename sorting ahead of it would silently change.
EXAMPLE = "github-issues.yaml"

# A commit and a branch, each in the form the operation that takes it requires.
# ⚠️ Fixed rather than read from this repository: a fixture taken from the tree is
# one whose failures depend on where it ran.
A_COMMIT = "0" * 39 + "a"
ANOTHER_COMMIT = "1" * 39 + "b"
A_BRANCH = "release/next"
A_WORKFLOW = "Deploy"
A_RUN = "7001"
A_SUCCESSOR = "7002"
A_WORKFLOW_ID = 55

# ⛔ **The host's own words, written out here and nowhere derived from the module
# under test.** Every conclusion fixture used to be read off the module's own
# constants, so the two literals this package exists to be the one home for were
# the one thing the suite could not catch: renaming the passing word to one this
# host never says left all of it green. Measured.
PASSED = "success"
FAILED = "failure"
CANCELLED = "cancelled"
SKIPPED = "skipped"
RUNNING = "in_progress"
QUEUED = "queued"


class _Host:
    """A transport that answers as the host does, and records what was asked.

    ⛔ A fake rather than a mock: it answers by the endpoint or subcommand asked
    for, so a refactor that reorders calls does not redden it and a call that
    moves to the wrong endpoint does.

    ⛔ **It models the client's exit status**, which is what makes the two
    decisions about the watch assertable at all. Without it, forcing
    `tolerate_exit` to `False` on every call left this suite green: the fake took
    the keyword and dropped it, so the arm labelled *a run that failed is still
    an answer* was about something the double could not represent. Measured.

    ⛔ **And it records the timeout**, for the same reason: deleting the watch's
    own long timeout changed nothing a suite reading only the arguments could see.

    ⛔ Every call's `writes` is recorded, which is what makes § 28's read-only
    property an assertion rather than a claim.
    """

    def __init__(
        self,
        answers: dict | None = None,
        *,
        fail_on: str | None = None,
        exit_on: dict | None = None,
    ):
        self.answers = answers or {}
        self.fail_on = fail_on
        # `{what the call contains: the status the client exits with}`.
        self.exit_on = exit_on or {}
        self.calls: list[tuple[str, bool, int]] = []

    def __call__(self, args, *, parse, timeout, tolerate_exit, writes):
        shown = " ".join(args)
        self.calls.append((shown, writes, timeout))
        if self.fail_on and self.fail_on in shown:
            raise port.HostUnavailable(f"`gh {shown}` failed: the host said no")
        for key, status in self.exit_on.items():
            if key in shown and status and not tolerate_exit:
                # Exactly what the real transport does with a non-zero exit it
                # was not told to tolerate.
                raise port.HostUnavailable(f"`gh {shown}` failed: exit {status}")
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
        return [shown for shown, writes, _timeout in self.calls if writes]

    @property
    def asked(self) -> list[str]:
        return [shown for shown, _writes, _timeout in self.calls]

    def timeout_of(self, fragment: str) -> int | None:
        for shown, _writes, timeout in self.calls:
            if fragment in shown:
                return timeout
        return None


def _configuration(more: dict | None = None) -> config.Config:
    """A whole example, with this kind written onto the port it answers for.

    Taken from the examples rather than written here, for the reason the
    contract's own suite gives: a fixture written by hand is a second
    configuration, free to disagree with every one this toolkit ships.

    ⛔ **Named, and not the first one the directory happens to sort.** Several
    arms below turn on what this example does *not* state -- no `host.runner`,
    and so no supersession group -- and taking it by position made the whole
    suite hostage to a filename: an example sorting ahead of it, or a runner
    added to it, changes what those arms mean with nothing edited here.
    """
    name = EXAMPLE
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
        "workflow_id": A_WORKFLOW_ID,
        "created_at": "2026-03-04T10:00:00Z",
        "conclusion": PASSED,
        "run_attempt": 1,
    }
    record.update(over)
    return record


def _jobs(*steps: list[dict]) -> dict:
    return {"jobs": [{"steps": list(each)} for each in steps]}


def _step(conclusion: str | None, status: str | None = None) -> dict:
    return {"conclusion": conclusion, "status": status}


# The workflow listing's own key, ⛔ derived from the record's workflow id rather
# than written beside it: spelled out, changing the fixture left the fake with no
# answer for the call and the arms died on an `AssertionError` instead of going
# red.
WORKFLOW_RUNS = f"actions/workflows/{A_WORKFLOW_ID}/runs"


def _answers(**over) -> dict:
    """An answer for each endpoint a read makes, keyed by what identifies it.

    ⛔ Ordered longest key first where two overlap: the jobs endpoint's path
    contains the run endpoint's, so a shorter key would answer both and the step
    count would come back from the run record.
    """
    answers = {
        f"actions/runs/{A_RUN}/jobs": _jobs([_step(PASSED)]),
        f"actions/runs/{A_RUN}": _run_record(),
        f"actions/runs?head_sha={A_COMMIT}": {"workflow_runs": [_run_record()]},
        WORKFLOW_RUNS: {"workflow_runs": [_run_record()]},
    }
    answers.update(over)
    return dict(sorted(answers.items(), key=lambda pair: -len(pair[0])))


# A runner block stating a supersession group, and one stating none. ⛔ Both are
# fixtures of their own: the arm for *stated but no group* was unasserted, and the
# arm for *no block at all* was created by the example rather than by a plant.
def _runner(**over) -> dict:
    block = {
        "label": "<a label>",
        "concurrent_jobs": 1,
        "budget_minutes": 30,
        "supersedes": "<a group>",
    }
    block.update(over)
    # ⛔ A key given `None` is **omitted**, which is what § 2 states the absence
    # as: written blank the reader refuses it, so a fixture meaning *no group*
    # would have refused the configuration instead of exercising the arm.
    return {"host.runner": {k: v for k, v in block.items() if v is not None}}


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

    def answer(outcome) -> dict:
        """What an operation answered, as a mapping whatever it did.

        ⛔ Every read of a result goes through this. A `.result[...]` on an
        outcome that did not perform raised where the comparison was, so a
        regression in one arm ended the whole run with a `TypeError` instead of
        reddening a line -- measured, with thirty-odd assertions never reached and
        no count printed. The empty mapping fails a comparison; it does not raise.
        """
        result = getattr(outcome, "result", None)
        return result if isinstance(result, dict) else {}

    def position(calls: list[str], fragment: str) -> int:
        """Where a call sits in what was asked, or -1 where it was never asked.

        ⛔ Grounded for the reason above: `next(...)` with no default raised
        `StopIteration` out of the suite when the arm under test stopped making
        the call, which is the one failure the harness exists to not have.
        """
        for index, shown in enumerate(calls):
            if fragment in shown:
                return index
        return -1

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
            answer(listed)["runs"] == [{
                "workflow": A_WORKFLOW,
                "run": A_RUN,
                "attempt": 1,
                "created_at": "2026-03-04T10:00:00Z",
            }],
            f"listed {answer(listed)!r}",
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
            quiet.performed and answer(quiet)["runs"] == [],
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
            read.performed and answer(read)["reading"] == host_checks.GREEN,
            f"read {answer(read)!r}",
        )
        # ⛔ The host's own conclusion word does not reach the caller. One word
        # arrives on two of the four readings, so a caller handed it would have to
        # make the distinction this port exists to make once.
        check(
            "and the host's conclusion word is nowhere in the answer",
            PASSED not in str(answer(read)),
            f"read {answer(read)!r}",
        )
        failed = _port(_Host(_answers(**{
            f"actions/runs/{A_RUN}": _run_record(conclusion="failure"),
        }))).invoke("conclusion", A_RUN)
        check(
            "a run that executed a step and did not pass reads as failed",
            answer(failed)["reading"] == host_checks.FAILED,
            f"read {answer(failed)!r}",
        )
        # ⛔ Zero **executed** steps, with a step list the host did state: skipped
        # steps ran nothing, so this is the never-started reading rather than a
        # count the host withheld.
        skipped = _port(_Host(_answers(**{
            f"actions/runs/{A_RUN}/jobs": _jobs([_step(SKIPPED), _step(None)]),
            f"actions/runs/{A_RUN}": _run_record(conclusion="cancelled"),
        }))).invoke("conclusion", A_RUN)
        check(
            "a run whose every step was skipped reads as never started",
            answer(skipped)["reading"] == host_checks.NEVER_STARTED,
            f"read {answer(skipped)!r}",
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
                answer(withheld)["reading"] is None
                and "precondition 3" in answer(withheld)["unanswered"],
                f"read {answer(withheld)!r}",
            )
            check(
                f"and {label} is never read as the never-started reading",
                answer(withheld)["reading"] != host_checks.NEVER_STARTED,
                f"read {answer(withheld)!r}",
            )

        # A run the host has not concluded: precondition 4, and no watch unasked.
        unconcluded = _Host(_answers(**{
            f"actions/runs/{A_RUN}": _run_record(conclusion=None),
        }))
        waiting = _port(unconcluded).invoke("conclusion", A_RUN)
        check(
            "an unconcluded run withholds the reading and names precondition 4",
            answer(waiting)["reading"] is None
            and "precondition 4" in answer(waiting)["unanswered"],
            f"read {answer(waiting)!r}",
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
            position(watched.asked, "run watch") >= 0
            and position(watched.asked, "run watch")
            < position(watched.asked, f"actions/runs/{A_RUN}"),
            f"asked {watched.asked!r}",
        )
        check(
            "and a run that failed is still an answer rather than a failed call",
            waited.performed and answer(waited)["reading"] == host_checks.FAILED,
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
            f"actions/runs/{A_RUN}/jobs": _jobs([_step(PASSED)]),
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
                WORKFLOW_RUNS: {"workflow_runs": [
                    _run_record(),
                    _run_record(id=int(A_SUCCESSOR), created_at="2026-03-04T11:00:00Z"),
                ]},
            })),
            grouped,
        ).invoke("conclusion", A_RUN)
        check(
            "with a group stated, a newer run for the same commit is the successor",
            answer(superseded)["reading"] == host_checks.SUPERSEDED
            and answer(superseded)["read_instead"] == A_SUCCESSOR,
            f"read {answer(superseded)!r}",
        )
        # And an older run is not a successor: the comparison is on when, not on
        # there being another run at all.
        older = _port(
            _Host(_answers(**{
                f"actions/runs/{A_RUN}": _run_record(conclusion="failure"),
                WORKFLOW_RUNS: {"workflow_runs": [
                    _run_record(id=6000, created_at="2026-03-04T09:00:00Z"),
                ]},
            })),
            grouped,
        ).invoke("conclusion", A_RUN)
        check(
            "while an older run for the same commit is not one",
            answer(older)["reading"] == host_checks.FAILED,
            f"read {answer(older)!r}",
        )

        # --- the log --------------------------------------------------------

        printed = "\n".join(f"line {number}" for number in range(1, 11))
        logged = _port(_Host({"run view": printed})).invoke("log", A_RUN, 3)
        check(
            "a log comes back as its tail",
            answer(logged)["text"] == "line 8\nline 9\nline 10",
            f"read {answer(logged)!r}",
        )
        # ⛔ Both counts, because a cut log that did not say so reads as the whole
        # of what the run printed -- and what a reader does with a log is conclude
        # from what is not in it.
        check(
            "with how many lines came back and how many there were",
            answer(logged)["lines"] == 3 and answer(logged)["of"] == 10,
            f"read {answer(logged)!r}",
        )
        whole = _port(_Host({"run view": printed})).invoke("log", A_RUN)
        check(
            "a log shorter than the tail asked for comes back whole, counts agreeing",
            answer(whole)["lines"] == 10 and answer(whole)["of"] == 10,
            f"read {answer(whole)!r}",
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
            answer(started)["find_it_with"] == "runs_for_ref"
            and "run" not in started.result,
            f"answered {answer(started)!r}",
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
            # ⛔ The four shapes a substring test let through, each measured: a go
            # written for a longer ref, a ref that is a word inside the go's own
            # prose, an input value spelled by letters of the workflow name, and
            # an input sent with no value at all. Every one of them is an approval
            # obtained for one dispatch clearing another.
            ("a go for a ref this one is a prefix of", lambda h: (
                A_WORKFLOW, A_BRANCH,
                f"approved: run {A_WORKFLOW} against {A_BRANCH}-week",
            )),
            ("a go whose prose contains the ref as a fragment", lambda h: (
                A_WORKFLOW, "main",
                f"approved: run {A_WORKFLOW} against the maintenance branch",
            )),
            ("an input value spelled inside the workflow's own name", lambda h: (
                A_WORKFLOW, A_BRANCH, f"approved: {A_WORKFLOW} against {A_BRANCH}",
                f"mode={A_WORKFLOW[2:5].lower()}",
            )),
            ("an input sent with an empty value and named nowhere in the go", lambda h: (
                A_WORKFLOW, A_BRANCH, f"approved: {A_WORKFLOW} against {A_BRANCH}",
                "dry_run=",
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
        # ⛔ An input with an empty value is held by its **name**, and a go that
        # names it clears it. An empty value is no no-op on this host -- it
        # overrides the workflow's declared default -- so the arm that exempted it
        # let an approval for one dispatch clear a dispatch that flipped every
        # defaulted input.
        empty_value = _Host({"workflow run": ""})
        with_blank = _port(empty_value).invoke(
            "dispatch", A_WORKFLOW, A_BRANCH,
            f"approved: {A_WORKFLOW} against {A_BRANCH} with note= cleared", "note=",
        )
        check(
            "an input with an empty value goes through where the go names the input",
            with_blank.performed and answer(with_blank)["inputs"] == {"note": ""},
            f"got {str(with_blank)!r}",
        )
        # ⛔ And the whole-token rule the other way: a go that names each thing
        # exactly clears the dispatch, so the rule above is not simply refusing
        # everything. A slashed ref and a dotted value stay one token each.
        exact = _Host({"workflow run": ""})
        through = _port(exact).invoke(
            "dispatch", A_WORKFLOW, A_BRANCH,
            f"go: {A_WORKFLOW} at {A_BRANCH}, env=staging, build=1.2.3",
            "env=staging", "build=1.2.3",
        )
        check(
            "a go naming each token exactly clears the dispatch",
            through.performed
            and answer(through)["inputs"] == {"env": "staging", "build": "1.2.3"},
            f"got {str(through)!r}",
        )

        # --- the host that does not answer ---------------------------------
        #
        # ⛔ A failed call and never the stated fallback: the capability is there
        # and the call did not go through, which § 3 holds apart from an absence
        # because a role that took the fallback would be acting on a decision
        # nobody made.
        unreachable = _port(_Host(_answers(), fail_on="actions/runs?head_sha"))
        outcome = unreachable.invoke("runs_for_ref", ANOTHER_COMMIT)
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
        # ⛔ And a direct call bypassing the port is refused — asserted **after a
        # successful invocation** and with nothing reset by hand. The bound
        # configuration used to outlive the call, so this refusal was reachable
        # only in a process that had never invoked anything, while a real process
        # answered a direct call out of whichever project was last.
        _port(_Host(_answers())).invoke("runs_for_ref", A_COMMIT)
        check(
            "an operation called directly after an invocation is refused, naming the port",
            refused(lambda: implementation.runs_for_ref(A_COMMIT)) == PORT,
            "the configuration outlived the call, so a direct call answered",
        )

        # --- a body the host answers with and this reader cannot walk --------
        #
        # ⛔ Each of these used to reach a role as a raw `AttributeError`: the
        # envelope was guarded and its members were not. A traceback is the one
        # thing this package may not hand a role, and `Port.invoke` converts only
        # `HostUnavailable`.
        for label, operation, args, answers in (
            ("a run record that is not an object", "conclusion", (A_RUN,),
             {f"actions/runs/{A_RUN}": ["not", "an", "object"]}),
            ("a run listing that is not an object", "runs_for_ref", (A_COMMIT,),
             {f"actions/runs?head_sha={A_COMMIT}": ["nope"]}),
            ("a run list that is not a list", "runs_for_ref", (A_COMMIT,),
             {f"actions/runs?head_sha={A_COMMIT}": {"workflow_runs": {"7001": {}}}}),
            ("a listed run the host named nothing for", "runs_for_ref", (A_COMMIT,),
             {f"actions/runs?head_sha={A_COMMIT}": {"workflow_runs": [{}]}}),
            ("a jobs body that is not an object", "conclusion", (A_RUN,),
             {f"actions/runs/{A_RUN}/jobs": ["queued"]}),
            ("a job that is not an object", "conclusion", (A_RUN,),
             {f"actions/runs/{A_RUN}/jobs": {"jobs": ["queued"]}}),
            ("a step list that is not a list", "conclusion", (A_RUN,),
             {f"actions/runs/{A_RUN}/jobs": {"jobs": [{"steps": "none"}]}}),
        ):
            shapeless = _port(_Host(_answers(**answers))).invoke(operation, *args)
            check(
                f"{label} is a failed call rather than a traceback",
                not shapeless.performed and shapeless.failed,
                f"got {str(shapeless)!r}",
            )

        # --- the watch's own two decisions -----------------------------------
        #
        # ⛔ Both are held against a transport that models an exit status, which
        # is what makes them assertable at all: with the status dropped, forcing
        # `tolerate_exit` to `False` everywhere left this suite green.
        exiting = _Host(
            _answers(**{f"actions/runs/{A_RUN}": _run_record(conclusion=FAILED)}),
            exit_on={"run watch": 1},
        )
        tolerated = _port(exiting).invoke("conclusion", A_RUN, "yes")
        check(
            "a watch whose client exits non-zero is still an answer about the run",
            tolerated.performed
            and answer(tolerated)["reading"] == host_checks.FAILED,
            f"got {str(tolerated)!r}",
        )
        check(
            "and the watch is given the longer timeout of the two",
            exiting.timeout_of("run watch") == implementation.WATCH_SECONDS
            and exiting.timeout_of(f"actions/runs/{A_RUN}")
            == implementation.CALL_SECONDS,
            f"watched for {exiting.timeout_of('run watch')!r}",
        )
        # ⛔ A wait that returned on a run the host still has not concluded is a
        # **failed call**: the watch did not follow the run to its end. Reported
        # as precondition 4 it told the caller to ask for the wait they just
        # asked for, which is a loop for a role and nonsense for a person.
        unfollowed = _port(_Host(_answers(**{
            f"actions/runs/{A_RUN}": _run_record(conclusion=None),
        }))).invoke("conclusion", A_RUN, "yes")
        check(
            "a wait that returned on an unconcluded run is a failed call",
            unfollowed.failed and not unfollowed.performed,
            f"got {str(unfollowed)!r}",
        )
        check(
            "and does not tell the caller to ask for the wait they asked for",
            "ask for the wait" not in unfollowed.detail,
            f"got {unfollowed.detail!r}",
        )

        # --- the step count's own two readings -------------------------------
        #
        # ⛔ A step that **started** counts. Reading the conclusion alone counted
        # a run cut off mid-step as having executed nothing, which is the
        # never-started reading about a run that reached a runner and ran.
        running = _port(_Host(_answers(**{
            f"actions/runs/{A_RUN}/jobs": _jobs([_step(None, RUNNING), _step(None, QUEUED)]),
            f"actions/runs/{A_RUN}": _run_record(conclusion=CANCELLED),
        }))).invoke("conclusion", A_RUN)
        check(
            "a step the host reports running counts as executed",
            answer(running)["steps"] == 1
            and answer(running)["reading"] != host_checks.NEVER_STARTED,
            f"read {answer(running)!r}",
        )
        # And a step still queued does not, which is what keeps the arm above
        # from counting everything.
        queued = _port(_Host(_answers(**{
            f"actions/runs/{A_RUN}/jobs": _jobs([_step(None, QUEUED)]),
            f"actions/runs/{A_RUN}": _run_record(conclusion=CANCELLED),
        }))).invoke("conclusion", A_RUN)
        check(
            "while a step still queued does not",
            answer(queued)["steps"] == 0
            and answer(queued)["reading"] == host_checks.NEVER_STARTED,
            f"read {answer(queued)!r}",
        )

        # --- the successor, at the two edges the timestamp cannot decide -----
        #
        # ⛔ This host states a run's creation to the second, so a successor
        # landing in the same second compared equal and was missed — and the miss
        # reads as `failed`, the one of § 2's four that is about the change, so a
        # reviewer spends a fix cycle on a run a successor already retired.
        same_second = _port(
            _Host(_answers(**{
                f"actions/runs/{A_RUN}": _run_record(conclusion=CANCELLED),
                WORKFLOW_RUNS: {"workflow_runs": [
                    _run_record(),
                    _run_record(id=int(A_SUCCESSOR)),
                ]},
            })),
            _runner(),
        ).invoke("conclusion", A_RUN)
        check(
            "a successor created in the same second is still the successor",
            answer(same_second)["reading"] == host_checks.SUPERSEDED
            and answer(same_second)["read_instead"] == A_SUCCESSOR,
            f"read {answer(same_second)!r}",
        )
        # ⛔ And a candidate the host numbered nothing for is skipped rather than
        # named: composing one anyway sent a reader to a run called `None`, whose
        # string is truthy and passes the blank-successor refusal one module over.
        unnumbered = _port(
            _Host(_answers(**{
                f"actions/runs/{A_RUN}": _run_record(conclusion=FAILED),
                WORKFLOW_RUNS: {"workflow_runs": [
                    _run_record(id=None, created_at="2026-03-04T11:00:00Z"),
                ]},
            })),
            _runner(),
        ).invoke("conclusion", A_RUN)
        check(
            "a newer run the host numbered nothing for is no successor",
            answer(unnumbered)["reading"] == host_checks.FAILED
            and answer(unnumbered)["read_instead"] is None,
            f"read {answer(unnumbered)!r}",
        )
        # ⛔ A runner block stating no group looks nothing up either, which is the
        # arm between *no block* and *a group*: § 2 makes the omission of
        # `supersedes` the statement that no run of this project's retires another.
        ungrouped = _Host(_answers(**{
            f"actions/runs/{A_RUN}": _run_record(conclusion=CANCELLED),
        }))
        _port(ungrouped, _runner(supersedes=None)).invoke("conclusion", A_RUN)
        check(
            "a runner stated with no supersession group looks up no successor",
            position(ungrouped.asked, "actions/workflows/") < 0,
            f"asked {ungrouped.asked!r}",
        )

        # --- what writes, read off the call and not off a keyword ------------
        #
        # ⛔ The read-only property used to be held against the flag rather than
        # the command: a `run rerun` and an `api --method DELETE` added to a read
        # were recorded as reads, and the assertion stayed green. Both directions
        # of the disagreement are refused now.
        for label, args, declared in (
            ("a writing call declared as a read", ["run", "rerun", A_RUN], False),
            ("a destructive endpoint declared as a read",
             ["api", "--method", "DELETE", f"repos/o/r/actions/runs/{A_RUN}"], False),
            ("a read declared as a write", ["api", f"repos/o/r/actions/runs/{A_RUN}"], True),
        ):
            _port(_Host(_answers()))
            reported = refused(
                lambda a=args, d=declared: implementation._host(a, writes=d, parse=False)
            )
            check(
                f"{label} is refused, naming the operation list",
                reported == operations,
                f"reported {reported!r}",
            )
        # And the dispatch's own call reads as a write by its command, so the
        # refusal above is not simply refusing everything.
        check(
            "the dispatch's own call reads as a write off the command itself",
            implementation._writes(["workflow", "run", A_WORKFLOW])
            and not implementation._writes(["api", "repos/o/r/actions/runs"]),
        )

        # --- the log's two refusals, which are two and not one ---------------
        check(
            "a tail this reader cannot parse is refused as that rather than as zero",
            "whole number" in message(
                lambda: _port(_Host({"run view": "x"})).invoke("log", A_RUN, "3.9")
            ),
            message(lambda: _port(_Host({"run view": "x"})).invoke("log", A_RUN, "3.9")),
        )

        # --- a run's identifier is text in every answer ----------------------
        #
        # ⚠️ A consumer carries an id from the listing into a reading, so the two
        # have to be the same kind of value.
        listing = answer(_port(_Host(_answers())).invoke("runs_for_ref", A_COMMIT))
        check(
            "a run's identifier comes back as text, as every other answer carries it",
            listing["runs"] and isinstance(listing["runs"][0]["run"], str),
            f"listed {listing!r}",
        )
    finally:
        implementation.TRANSPORT = was
        implementation._bound = None

    if failures:
        print(f"\n{failures} assertion(s) did not hold.")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(self_test())
