#!/usr/bin/env python3
"""GitHub Actions behind the run port: list, read, log, and dispatch by hand.

The one host kind this repository runs on, which is why this implementation
exists first: a port nothing stands on is a port whose holes are nobody's
problem. Every call goes through `gh`, which holds the credential and the host's
base URL, so an enterprise host needs no key here. The configuration arrives
from the port through `bind`; nothing here resolves a project for itself.

What it implements, and the decisions that are this kind's rather than § 28's:

  * **All four operations § 28 states.** None of them is a capability this host
    lacks. ⛔ No count of them is carried: the list is closed and stated once, in
    § 28, and a number here would be wrong the next time it grows.
  * ⛔ **Three of the four write nothing, and that is held rather than claimed.**
    Every host call goes through `_host`, which is told whether it writes, and
    the suite beside this file asserts that a listing, a conclusion and a log
    make no writing call. § 28 states the property; this is where it can fail.
  * ⛔ **`conclusion` hands the three facts to the one reading and keeps none of
    its own.** How many steps the run's jobs executed, whether the host calls it
    a pass, and the id of any run that retired it are read here -- the host's
    vocabulary belongs in this package -- and which of § 2's four readings they
    make is the consumer beside this package's. ⚠️ **The host's conclusion word
    does not leave this file**: `cancelled` arrives on two of those readings, so
    a caller handed the word would have to make the distinction this port exists
    to make once.
  * ⛔ **An empty step list is *unavailable* and never zero.** The host returns
    no jobs for a run it has not expanded yet and a job with no step list at all,
    and zero executed steps is § 2's never-started reading -- so reading the
    first as the second would report *the queue ate this run* about a run that
    may have executed every step it has. Those come back with the reading
    withheld and precondition 3 named, which is § 2's rule that a precondition
    which cannot be answered is reported as the step it was.
  * ⛔ **A run that has not concluded is not a reading either.** Asked to wait,
    this kind blocks in the host's own client -- § 2's *watch rather than poll*,
    which costs nothing and cannot miss a transition between two polls. Asked
    not to, an unconcluded run comes back with precondition 4 named. ⚠️ **The
    watch's exit status is deliberately not read**: the client exits non-zero for
    a run that failed, and a failed run is an answer rather than a call that did
    not go through.
  * ⚠️ **A supersession is read only where the project states a group.** § 2
    makes the omission of `host.runner.supersedes` a statement -- no run of this
    project's retires another -- so this kind asks nothing where it is absent.
    Where it is stated, the successor is the newest run of the same workflow for
    the same commit, and ⛔ **a group keyed on anything else is not readable from
    the host at all**: the concurrency expression lives in the workflow file and
    the host publishes no *retired by* field. A supersession this misses reads as
    never-started rather than as green, which sends a reader to the queue instead
    of to the successor -- the wrong remedy, and not coverage.
  * ⛔ **A log is returned as a tail with both counts beside it.** A whole run log
    is unbounded and a truncated one that did not say so reads as a whole one, so
    the answer carries how many lines came back and how many there were.
  * ⛔ **A dispatch takes a branch or a tag and a listing takes a commit**, which
    is this host's own shape rather than an inconsistency: its dispatch endpoint
    rejects a commit, and precondition 2 asks about a commit and not about
    whatever a branch points at now. Each operation refuses the other's form.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys

# The package's parent, appended rather than prepended: this module is imported
# as `runs.github`, so the contract beside it is not otherwise on the path, and
# putting it first would shadow a standard-library name.
_SCRIPTS = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _SCRIPTS not in sys.path:
    sys.path.append(_SCRIPTS)

import host_checks  # noqa: E402
import port  # noqa: E402

KIND = "github"

# What this host calls a pass. ⛔ The one conclusion word read here and the one
# that may be: § 2 has a caller read *whether the host calls it a pass* off the
# host, and every other word -- `cancelled` above all -- is excluded on purpose,
# since one of them arrives on two different readings.
PASSED = "success"

# A step the host reports as not having executed. A skipped step ran nothing, so
# it is not part of the count § 2's precondition 3 asks for.
SKIPPED = "skipped"

# A commit, as this host's run listing is keyed on it. ⛔ Full length and nothing
# shorter: the listing filter takes a whole object name, and an abbreviated one
# comes back as a listing with nothing in it -- which reads exactly like a commit
# the host made no run for.
COMMIT = re.compile(r"^[0-9a-f]{40}$")

# How much of a log comes back by default, and ⚠️ **a tail rather than a head**:
# what a reader of a failed run needs is where it stopped. The number is this
# kind's own and is reported beside every answer, so a caller never has to know
# it to tell a cut log from a whole one.
LOG_LINES = 200

# The two timeouts. ⛔ A watch gets its own, long one: it blocks until the host's
# runs settle, which is the whole point of asking for it, and the ordinary one
# would turn every wait into a call that did not go through.
CALL_SECONDS = 30
WATCH_SECONDS = 1800

# What a caller writes to ask for the wait. Text rather than a flag, because every
# argument reaching an operation through the port's own invocation is text.
YES = ("yes", "true", "1", "wait")

# The configuration the port last handed down, and the only place one comes from.
# ⛔ Never resolved here, and never from the working directory: which repository's
# runs these are is `host.repo`'s to say (§ 2), and a process serving more than
# one project would otherwise pin every later call to the first one's repository.
_bound = None

# The transport, as a name this module's own suite can replace. ⛔ A seam rather
# than a convenience: every operation here makes a host call, so a suite that
# could not stand in for one would either assert nothing or dispatch a real run
# against whatever this repository configures.
TRANSPORT = None


def bind(configuration) -> None:
    """Take the configuration for the operation about to run.

    `Port.invoke` calls this before every operation, so it is per call rather
    than per process and switching projects needs no reset.
    """
    global _bound
    _bound = configuration


# The directory this module sits in, which is the whole of what declares which
# port it answers for -- the sibling packages' rule, for the reason they state.
_PACKAGE = os.path.basename(os.path.dirname(os.path.abspath(__file__)))


def _spec():
    """This port's declaration, resolved by the directory this module sits in."""
    for spec in port.surface_ports().values():
        if spec.package == _PACKAGE:
            return spec
    raise port.ConfigError(
        f"{_PACKAGE}/{os.path.basename(__file__)}",
        "sits in a package no `# port:` marker names, so which port it answers "
        "for cannot be resolved. A module's own directory is what declares that "
        "(§ 26), and no port on the surface is read out of this one.",
    )


def _operations() -> str:
    """The key a refusal about a *call* names: this port's operation list.

    ⛔ Never a key the surface does not declare. A `ConfigError`'s key is
    contractually the thing to go and edit, and what is wrong when a caller hands
    over a branch where a commit belongs is the call.
    """
    return f"{_spec().prefix}.operations"


def _configuration():
    if _bound is None:
        raise port.ConfigError(
            _spec().name,
            "was asked for an operation before the port bound a configuration to "
            "it. Every operation is reached through `Port.invoke`, which binds "
            "first; a direct call bypasses the one place the project is stated.",
        )
    return _bound


def _repo() -> str:
    """The repository the bound configuration addresses.

    The surface marks `host.repo` `# required`, so a configuration that reached
    here states one; what this refuses is the shape, which nothing else checks.
    """
    repo = _configuration().get("host.repo")
    if not isinstance(repo, str) or repo.count("/") != 1:
        raise port.ConfigError(
            "host.repo",
            f"is {repo!r}, which is not `owner/name`. Every call here addresses "
            "the repository by that pair, so a URL or a bare name has no reading "
            "this host could act on.",
        )
    return repo


def _client(args: list[str], *, parse: bool, timeout: int, tolerate_exit: bool, writes: bool):
    """The real transport: one `gh` call, every failure the contract's own.

    ⛔ `port.HostUnavailable` rather than a class of this module's: the port turns
    it into a `failed` outcome, and a role must be able to tell a broken call from
    a missing capability without knowing which host answered. The command is in
    every message, so a failure is reproducible by hand.

    ⚠️ `writes` is taken and not read here. It is declared at the call so that
    something can hold § 28's read-only property, and the transport the suite
    stands in for is what reads it; branching on it here would make the real
    client the second reader of a fact the call already states.
    """
    shown = "gh " + " ".join(args)
    try:
        done = subprocess.run(
            ["gh"] + args, capture_output=True, text=True, timeout=timeout
        )
    except FileNotFoundError:
        raise port.HostUnavailable(
            f"`gh` is not on PATH, so `{shown}` could not run"
        ) from None
    except subprocess.TimeoutExpired:
        raise port.HostUnavailable(f"`{shown}` timed out after {timeout}s") from None
    if done.returncode != 0 and not tolerate_exit:
        raise port.HostUnavailable(
            f"`{shown}` failed: {done.stderr.strip() or 'no stderr'}"
        )
    if not parse:
        return done.stdout
    if not done.stdout.strip():
        raise port.HostUnavailable(
            f"`{shown}` answered with nothing where a body was expected"
        )
    try:
        return json.loads(done.stdout)
    except ValueError:
        raise port.HostUnavailable(
            f"`{shown}` answered with something that is not a body this reader "
            "can parse"
        ) from None


def _host(
    args: list[str],
    *,
    writes: bool = False,
    parse: bool = True,
    timeout: int = CALL_SECONDS,
    tolerate_exit: bool = False,
):
    """One host call, declaring whether it writes.

    ⛔ `writes` is what makes § 28's read-only property checkable rather than
    claimed: three of the four operations must never pass it, and the suite
    beside this file asserts exactly that. Nothing here branches on it -- it is
    carried so that something can.
    """
    transport = TRANSPORT if TRANSPORT is not None else _client
    return transport(
        args,
        parse=parse,
        timeout=timeout,
        tolerate_exit=tolerate_exit,
        writes=writes,
    )


# --- the operations ---------------------------------------------------------
#
# Each takes what a role already has and returns what a role can carry onward.
# None of them reads a capability: being here *is* the declaration (§ 3).


def runs_for_ref(ref: str) -> dict:
    """Every run the host made for one commit.

    ⛔ Keyed on the commit and never on a branch (§ 28): a branch names whatever
    is newest when it is read, and § 2's precondition 2 asks whether a run exists
    for *this* commit.

    ⚠️ An empty list is an answer and not an absence. The capability is present,
    so what it means -- precondition 2 unmet, which on this host is most often a
    conflicted change producing no run at all -- is the caller's reading.

    ⚠️ **A commit this host does not have comes back the same way**, measured: the
    listing filter simply matches nothing, so an unpushed or unknown object name
    is indistinguishable here from a commit the host made no run for. ⛔ That is
    § 2's precondition **1** rather than a reading this operation can supply --
    nothing committed is unpushed, asked before precondition 2 and by the role --
    and telling the two apart would cost a second call to establish a fact the
    caller already had to have.
    """
    commit = str(ref).strip()
    if not COMMIT.match(commit):
        raise port.ConfigError(
            f"{_operations()}.runs_for_ref",
            f"was given {ref!r}, which is not a commit this host's run listing is "
            "keyed on: a full 40-character object name. A branch names whatever "
            "is newest at the moment it is read, and an abbreviated name comes "
            "back as a listing with nothing in it -- which reads exactly like a "
            "commit the host made no run for (§ 28).",
        )
    repo = _repo()
    answer = _host([
        "api",
        f"repos/{repo}/actions/runs?head_sha={commit}&per_page=100",
    ])
    found = answer.get("workflow_runs") if isinstance(answer, dict) else None
    if found is None:
        raise port.HostUnavailable(
            f"the run listing for `{commit}` in `{repo}` came back without a run "
            "list in it, so which runs exist for this commit is unestablished"
        )
    return {
        "repo": repo,
        "commit": commit,
        "runs": [
            {
                # The workflow's **name**, which is the key § 2's `checks` is read
                # by -- never the file path or the job's name.
                "workflow": run.get("name"),
                "run": run.get("id"),
                "attempt": run.get("run_attempt"),
                "created_at": run.get("created_at"),
            }
            for run in found
        ],
    }


def conclusion(run, wait: str = "no") -> dict:
    """Which of § 2's four readings one run concluded in.

    The three facts are read here and the reading is the consumer's, so that the
    turning of one into the other happens once for every caller (§ 28).

    ⛔ Two answers withhold the reading rather than inventing one, each naming the
    precondition it could not answer: a run the host has not concluded, where the
    caller did not ask to wait, and a step count the host does not state.
    """
    identifier = str(run).strip()
    if not identifier:
        raise port.ConfigError(
            f"{_operations()}.conclusion",
            "was given no run to read. A reading is about one run, and a blank "
            "identifier would address the repository's newest -- an answer about "
            "a commit nobody asked about.",
        )
    repo = _repo()
    if str(wait).strip().lower() in YES:
        # ⛔ The host's own blocking client, and its exit status discarded: § 2
        # forbids a sleep and a poll alike, and a non-zero exit here is a run that
        # failed rather than a call that did not go through.
        _host(
            ["run", "watch", identifier, "--repo", repo],
            parse=False,
            timeout=WATCH_SECONDS,
            tolerate_exit=True,
        )
    record = _host(["api", f"repos/{repo}/actions/runs/{identifier}"])
    workflow = record.get("name")
    read = {
        "repo": repo,
        "run": identifier,
        "workflow": workflow,
        "commit": record.get("head_sha"),
    }
    if not record.get("conclusion"):
        return dict(
            read,
            reading=None,
            unanswered=(
                "the host has not concluded this run, so § 2's precondition 4 is "
                "unanswered. ⛔ Not a failing check and not green: ask for the "
                "wait, which blocks in the host's own client rather than sleeping."
            ),
        )
    steps = _steps(repo, identifier)
    if steps is None:
        return dict(
            read,
            reading=None,
            unanswered=(
                "the host states no step list for this run, so how many steps its "
                "jobs executed is unestablished and § 2's precondition 3 is "
                "unanswered. ⛔ Never read as zero steps, which is the "
                "never-started reading and would report the queue about a run "
                "that may have executed everything it has."
            ),
        )
    reading = host_checks.conclusion(
        steps,
        record.get("conclusion") == PASSED,
        _superseded_by(repo, record),
    )
    return dict(read, steps=steps, **reading)


def log(run, lines: int = LOG_LINES) -> dict:
    """What one run printed, as a tail with both counts beside it.

    ⛔ The counts are part of the answer: a log cut to its tail and reported as a
    log reads as the whole of what the run printed, and the one thing a reader
    does with a log is conclude from what is not in it -- whether a failure was
    the change's or the environment's (§ 2).

    ⚠️ What comes back is text somebody else's run wrote, so § 14's ingestion
    step is the caller's next act. This operation does not perform it: a role
    that was handed pre-cleared text would have no step of its own to report.
    """
    identifier = str(run).strip()
    if not identifier:
        raise port.ConfigError(
            f"{_operations()}.log",
            "was given no run to read. A log belongs to one run, and a blank "
            "identifier would address the repository's newest.",
        )
    try:
        wanted = int(lines)
    except (TypeError, ValueError):
        wanted = -1
    if wanted < 1:
        raise port.ConfigError(
            f"{_operations()}.log",
            f"was asked for {lines!r} lines. A tail is at least one line, and a "
            "count of zero or less would come back as a log with nothing in it -- "
            "which reads as a run that printed nothing.",
        )
    repo = _repo()
    text = _host(
        ["run", "view", identifier, "--repo", repo, "--log"], parse=False
    )
    whole = text.splitlines()
    return {
        "repo": repo,
        "run": identifier,
        "lines": len(whole[-wanted:]),
        "of": len(whole),
        "text": "\n".join(whole[-wanted:]),
    }


def dispatch(workflow: str, ref: str, go: str, *inputs: str) -> dict:
    """Start one run by hand, refused without a go that names this dispatch.

    ⛔ The refusal is the port's and not each role's (§ 28), and what the go must
    name is the workflow, the ref and every input value -- so an approval given
    for another ref or another input does not clear this call. ⚠️ **What it
    cannot catch is a go replayed against a byte-identical dispatch**, which § 28
    states as the limit it is: those three are the whole of what either side can
    name, and what stops the second one is the role asking per dispatch.

    ⛔ The ref is a branch or a tag, this host's dispatch endpoint rejecting a
    commit -- the opposite form from the listing above, which is that host's own
    shape rather than an inconsistency here.
    """
    named = str(workflow).strip()
    at = str(ref).strip()
    if not named or not at:
        raise port.ConfigError(
            f"{_operations()}.dispatch",
            f"was given {workflow!r} as a workflow and {ref!r} as a ref. A "
            "dispatch names the workflow it starts and the ref it is against, "
            "and a blank either side would start whatever the host picked.",
        )
    if COMMIT.match(at):
        raise port.ConfigError(
            f"{_operations()}.dispatch",
            f"was given the commit {at!r} as its ref. This host's dispatch takes "
            "a branch or a tag and rejects a commit, which is the opposite form "
            "from the run listing's and is the host's own shape (§ 28). Name the "
            "branch or tag the run is against.",
        )
    values = []
    for stated in inputs:
        name, separator, value = str(stated).partition("=")
        if not separator or not name.strip():
            raise port.ConfigError(
                f"{_operations()}.dispatch",
                f"was given {stated!r} as an input. § 28 states a dispatch's "
                "inputs as typed, so each one is written `name=value`; a bare "
                "word names no input and would be sent as a value with no key.",
            )
        values.append((name.strip(), value))
    _hold_the_go(go, named, at, values)
    repo = _repo()
    args = ["workflow", "run", named, "--repo", repo, "--ref", at]
    for name, value in values:
        args += ["--field", f"{name}={value}"]
    _host(args, writes=True, parse=False)
    return {
        "repo": repo,
        "workflow": named,
        "ref": at,
        "inputs": dict(values),
        "dispatched": True,
        # ⛔ No run id is composed here. The host's client prints none for a
        # dispatch, and inventing one would be a report naming a run nobody can
        # read; the run this started is found by asking for the runs of the
        # commit the ref now points at.
        "find_it_with": "runs_for_ref",
    }


def _hold_the_go(go, workflow: str, ref: str, values: list[tuple[str, str]]) -> None:
    """Refuse a dispatch whose go does not name it.

    ⛔ The refusal names what was missing and does not compose the string that
    would satisfy it. A refusal that handed back the sentence to repeat would be
    a form to fill in rather than an approval to have obtained.
    """
    stated = "" if go is None else str(go).strip()
    if not stated:
        raise port.ConfigError(
            f"{_operations()}.dispatch",
            "was asked to start a run with no go for this dispatch. § 28 makes "
            "the confirmation the one rail between a routine command and a "
            "production write, and it is per dispatch: ask, and pass what was "
            "approved -- it has to name this workflow, this ref and each input "
            "value.",
        )
    missing = [
        label
        for label, token in [("the workflow", workflow), ("the ref", ref)]
        + [(f"the `{name}` input's value", value) for name, value in values if value]
        if token.lower() not in stated.lower()
    ]
    if missing:
        raise port.ConfigError(
            f"{_operations()}.dispatch",
            f"was given a go that does not name {', '.join(missing)}, so it is "
            "not an approval of this dispatch. § 28 binds a go to the workflow, "
            "the ref and the inputs it was given for: an approval obtained for "
            "another ref or another input does not clear this call, and that is "
            "what *per dispatch* means mechanically.",
        )


def _steps(repo: str, run: str) -> int | None:
    """How many steps the run's jobs executed, or `None` where that is unstated.

    ⛔ `None` is *unavailable* and never zero. The host answers with no job list
    for a run it has not expanded, and with a job carrying no step list at all;
    zero executed steps is § 2's never-started reading, so collapsing the two
    would report the queue about a run that executed everything it has.
    """
    answer = _host([
        "api", f"repos/{repo}/actions/runs/{run}/jobs?per_page=100"
    ])
    jobs = answer.get("jobs") if isinstance(answer, dict) else None
    if not jobs:
        return None
    executed = 0
    for job in jobs:
        steps = job.get("steps")
        if not steps:
            return None
        for step in steps:
            concluded = step.get("conclusion")
            if concluded and concluded != SKIPPED:
                executed += 1
    return executed


def _superseded_by(repo: str, record: dict) -> str | None:
    """The run that retired this one, where the project states a group.

    ⚠️ Asked nothing where `host.runner.supersedes` is absent: § 2 states that
    omission as *no run of this project's retires another*, so a lookup there
    would be this module answering a question the project already answered.

    ⛔ And the successor is the newest run of the same workflow for the same
    commit, which is the whole of what this host publishes: the concurrency
    expression lives in the workflow file and there is no *retired by* field. A
    group keyed on anything else is a supersession this misses, which reads as
    never-started rather than as green -- the wrong remedy and not coverage.
    """
    stated = host_checks.runner(_configuration())
    if not stated["stated"] or not stated["runner"].get("supersedes"):
        return None
    commit, workflow = record.get("head_sha"), record.get("workflow_id")
    created, mine = record.get("created_at"), record.get("id")
    if not commit or not workflow or not created:
        return None
    answer = _host([
        "api",
        f"repos/{repo}/actions/workflows/{workflow}/runs"
        f"?head_sha={commit}&per_page=100",
    ])
    newer = [
        run
        for run in (answer.get("workflow_runs") or [])
        if run.get("id") != mine and (run.get("created_at") or "") > created
    ]
    if not newer:
        return None
    return str(max(newer, key=lambda run: run.get("created_at") or "").get("id"))


ADAPTER = port.Adapter(binder=bind, operations={
    "runs_for_ref": runs_for_ref,
    "conclusion": conclusion,
    "log": log,
    "dispatch": dispatch,
})


def self_test() -> int:
    """This implementation's own decisions, held beside it.

    What the contract's suite holds is the contract -- the operation list, the
    absent case, the writer refusal. These are this host's own: the read-only
    property, the two withheld readings, the go bound to its dispatch, and the
    two ref forms that are each other's refusal.
    """
    from runs import _github_suite as suite

    return suite.self_test()


if __name__ == "__main__":
    sys.exit(self_test())
