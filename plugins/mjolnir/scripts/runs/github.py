#!/usr/bin/env python3
"""GitHub Actions behind the run port: list, read, log, and dispatch by hand.

The one host kind this repository runs on, which is why this implementation
exists first: a port nothing stands on is a port whose holes are nobody's
problem. Every call goes through `gh`, which holds the credential and the host's
base URL, so an enterprise host needs no key here. The configuration arrives
from the port through `bind`; nothing here resolves a project for itself.

What it implements, and the decisions that are this kind's rather than § 28's:

  * **Every operation § 28 states.** None of them is a capability this host
    lacks. ⛔ No count of them is carried: the list is closed and stated once, in
    § 28, and a number here would be wrong the next time it grows.
  * ⛔ **Only the dispatch writes, and that is held rather than claimed.** Every
    host call goes through `_host`, which reads off the call itself whether it
    writes and refuses a disagreement with what the operation declared -- so the
    property is about the command and not about a keyword somebody remembered.
    § 28 states it; this is where it can fail.
  * ⛔ **`conclusion` hands the facts to the one reading and keeps none of its
    own.** How many steps the run's jobs executed, whether the host calls it a
    pass, and the id of any run that retired it are read here -- the host's
    vocabulary belongs in this package -- and which of § 2's four readings they
    make is the consumer beside this package's. ⚠️ **The host's conclusion word
    does not leave this file**, for the reason that consumer states rather than
    one restated here.
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
    not go through. ⛔ **Which is why a wait that returned on a run still
    unconcluded is a failed call**: those two events are one to this operation,
    and reported as precondition 4 the second tells a caller to ask for the wait
    they just asked for.
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
  * ⛔ **A body the host answered with and this reader cannot walk is a failed
    call**, member by member and not only at the envelope. The envelope was
    guarded and the members were not, so an unexpected shape -- a proxy's, an
    enterprise host's, a redirected path's -- reached a role as a raw
    `AttributeError`, which is the traceback this package exists not to hand one.
  * ⛔ **The bound configuration is given back after every operation**, so a
    direct call that bypassed the port is refused in a process that has already
    invoked something. It used to be sticky for the life of the process, which
    made that refusal reachable only before the first call.
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

# What this host's status word says about a step that carries no conclusion: one
# that is running has executed, and one still queued has not. ⛔ Read because the
# conclusion alone counted a run cut off mid-step as having executed nothing,
# which is the never-started reading about a run that reached a runner.
STARTED = {"in_progress"}

# A commit, as this host's run listing is keyed on it. ⛔ Full length and nothing
# shorter: the listing filter takes a whole object name, and an abbreviated one
# comes back as a listing with nothing in it -- which reads exactly like a commit
# the host made no run for.
COMMIT = re.compile(r"^[0-9a-f]{40}$")

# Which of this client's calls write on the host, as the subcommand pair that
# stands at the head of one, and which request methods read. ⛔ The host's own
# vocabulary, which is what this package exists to be the one place for -- and
# what `_writes` below holds a caller's declaration against.
WRITING_CALLS = {
    ("workflow", "run"),
    ("run", "rerun"),
    ("run", "cancel"),
    ("run", "delete"),
}
READ_METHODS = {"GET", "HEAD"}

# One word of a go, and of a thing a go has to name. ⛔ The characters a ref, a
# workflow name and an input value are **made of**, so everything else is a
# separator: a slashed ref and a dotted version are one token each, while the
# prose around them is not part of any of them.
TOKEN = re.compile(r"[A-Za-z0-9_./-]+")

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


def _through_the_port(operation):
    """One operation, with the bound configuration given back afterwards.

    ⛔ **Given back, so that a direct call is refused in a process that has
    already invoked something.** `bind` is per call, but the value it set used to
    outlive the call: measured, one legitimate invocation left the configuration
    sticky for the life of the process, so a later direct call answered -- about
    whichever project happened to be last. The refusal that exists for that case
    was reachable only in a process that had never invoked anything.
    """
    def performed(*args, **kwargs):
        global _bound
        try:
            return operation(*args, **kwargs)
        finally:
            _bound = None

    performed.__name__ = operation.__name__
    performed.__doc__ = operation.__doc__
    return performed


def _body(answer, key: str, what: str):
    """A host body this reader can walk, or a failed call saying it could not.

    ⛔ Every member read below goes through this or its own `isinstance`: the
    envelope was guarded and the members were not, so a body the host answered
    200 with in an unexpected shape -- a proxy's, an enterprise host's, a
    redirected path's -- reached a role as a raw `AttributeError`. That is the
    traceback this package refuses to hand a role, and `Port.invoke` converts
    only `HostUnavailable`.
    """
    if not isinstance(answer, dict):
        raise port.HostUnavailable(
            f"{what} came back as something other than a body this reader can "
            f"walk, so {key} is unestablished"
        )
    return answer


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


def _writes(args: list[str]) -> bool:
    """Whether this call writes, read off the call itself.

    ⛔ **Derived and then compared against what the caller declared**, rather
    than taken on the caller's word. A flag defaulting to *this is a read* is a
    property held against an author who remembers to mark their own write, which
    is not a property at all: measured, a `run rerun` and an `api --method
    DELETE` added to a read were recorded as reads and the read-only assertion
    stayed green.
    """
    words = [word for word in args if word]
    if not words:
        return False
    if words[0] == "api":
        method = ""
        for index, word in enumerate(words):
            if word == "--method" and index + 1 < len(words):
                method = words[index + 1].upper()
            elif word.startswith("--method="):
                method = word.partition("=")[2].upper()
            elif word in ("-X",) and index + 1 < len(words):
                method = words[index + 1].upper()
        return bool(method) and method not in READ_METHODS
    return tuple(words[:2]) in WRITING_CALLS


def _host(
    args: list[str],
    *,
    writes: bool = False,
    parse: bool = True,
    timeout: int = CALL_SECONDS,
    tolerate_exit: bool = False,
):
    """One host call, holding what it writes to what the call itself says.

    ⛔ `writes` is what makes § 28's read-only property checkable rather than
    claimed, and ⛔ **it is checked here against the call** rather than carried:
    the reads must never pass it and must never make a call that writes, and a
    disagreement between the two is this module's own mistake and is refused
    before the call goes out.
    """
    derived = _writes(args)
    if derived != writes:
        raise port.ConfigError(
            f"{_operations()}",
            f"was about to run `gh {' '.join(args)}`, which "
            + ("writes on the host" if derived else "is a read")
            + ", declared as "
            + ("a write" if writes else "a read")
            + ". § 28 states every operation but the dispatch as read-only, so "
            "the two have to agree: a read that writes is a defect here and a "
            "write declared as a read is the property going unheld.",
        )
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
    what = f"the run listing for `{commit}` in `{repo}`"
    found = _body(answer, "which runs exist for this commit", what).get("workflow_runs")
    if not isinstance(found, list):
        raise port.HostUnavailable(
            f"{what} came back without a run list in it, so which runs exist for "
            "this commit is unestablished"
        )
    # ⛔ Every entry walked rather than the envelope alone. A listed run with no
    # id and no workflow name came back as an answer -- and the name is the key
    # § 2's `checks` is read by, so a `None` there matches nothing while reading
    # as a run that exists.
    for run in found:
        if not isinstance(run, dict) or not run.get("id") or not run.get("name"):
            raise port.HostUnavailable(
                f"{what} lists a run the host named or numbered nothing for, so "
                "which runs exist for this commit is unestablished"
            )
    return {
        "repo": repo,
        "commit": commit,
        "runs": [
            {
                # The workflow's **name**, which is the key § 2's `checks` is read
                # by -- never the file path or the job's name.
                "workflow": run.get("name"),
                # ⚠️ As text, which is the form every other operation's answer
                # carries a run in: a consumer comparing an id from the listing
                # against one from a reading would otherwise never match.
                "run": str(run.get("id")),
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

    ⛔ **A wait that returned on a run the host still has not concluded is a
    failed call and not an unanswered precondition.** The client's exit status is
    not read here, so a run that failed and a watch that could not follow one are
    the same event to this operation -- and reported as precondition 4 the second
    tells the caller to ask for the wait they just asked for, which is a loop for
    a role and nonsense for a person.
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
    waited = str(wait).strip().lower() in YES
    if waited:
        # ⛔ The host's own blocking client, and its exit status discarded: § 2
        # forbids a sleep and a poll alike, and a non-zero exit here is a run that
        # failed rather than a call that did not go through.
        _host(
            ["run", "watch", identifier, "--repo", repo],
            parse=False,
            timeout=WATCH_SECONDS,
            tolerate_exit=True,
        )
    record = _body(
        _host(["api", f"repos/{repo}/actions/runs/{identifier}"]),
        f"how run `{identifier}` concluded",
        f"the record of run `{identifier}` in `{repo}`",
    )
    workflow = record.get("name")
    read = {
        "repo": repo,
        "run": identifier,
        "workflow": workflow,
        "commit": record.get("head_sha"),
    }
    if not record.get("conclusion"):
        if waited:
            raise port.HostUnavailable(
                f"the wait on run `{identifier}` returned and the host still has "
                "not concluded it, so the watch did not follow the run to its end "
                "-- which is a call that did not go through rather than a "
                "precondition nothing could answer"
            )
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
    # ⛔ Two refusals and not one. Reading a count this reader cannot parse as
    # *zero or less* told a caller who asked for `3.9` lines that they had asked
    # for none, which sends them to fix the wrong thing.
    try:
        wanted = int(lines)
    except (TypeError, ValueError):
        raise port.ConfigError(
            f"{_operations()}.log",
            f"was asked for {lines!r} lines, which is not a whole number of "
            "them. A tail is a count of lines, and every argument reaching an "
            "operation through the port is text -- so a count is written as "
            "digits.",
        ) from None
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
    name is the workflow, the ref and every input this call sends -- so an
    approval given for another ref or another input does not clear this call.
    ⚠️ **What it cannot catch is stated in § 28 rather than here**: a go replayed
    against a byte-identical dispatch, and that a person gave the go at all.

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


def _tokens(text: str) -> set[str]:
    """What a go names, as whole tokens and never as a run of characters.

    ⛔ Split rather than searched. A substring test is what this rail shipped as
    and it is defeated by the ordinary spellings of the things it holds:
    measured, a go for `release/next-week` cleared a dispatch against
    `release/next`, a go naming *the maintenance branch* cleared `main`, and an
    input value of `loy` was cleared by the letters inside `Deploy`. Each of
    those is an approval obtained for one dispatch clearing another, which is the
    whole of what this rail is for.

    ⚠️ The separators are everything a ref, a workflow name and an input value do
    **not** contain, so a slashed ref and a dotted version stay one token each.
    """
    return {word.lower() for word in TOKEN.findall(str(text)) if word}


def _hold_the_go(go, workflow: str, ref: str, values: list[tuple[str, str]]) -> None:
    """Refuse a dispatch whose go does not name it.

    ⛔ The refusal names what was missing and does not compose the string that
    would satisfy it. A refusal that handed back the sentence to repeat would be
    a form to fill in rather than an approval to have obtained.

    ⛔ **An input is held by its name whenever it is sent, whatever its value.**
    An input stated with an empty value is not a no-op on this host -- it
    overrides whatever default the workflow declares for it, so an empty boolean
    is a false one -- and exempting it let an approval for one dispatch clear a
    dispatch that flipped every defaulted input. Measured.
    """
    stated = "" if go is None else str(go).strip()
    if not stated:
        raise port.ConfigError(
            f"{_operations()}.dispatch",
            "was asked to start a run with no go for this dispatch. § 28 makes "
            "the confirmation the one rail between a routine command and a "
            "production write, and it is per dispatch: ask, and pass what was "
            "approved -- it has to name this workflow, this ref and every input "
            "this call sends.",
        )
    named = _tokens(stated)
    wanted: list[tuple[str, str]] = [("the workflow", workflow), ("the ref", ref)]
    for name, value in values:
        wanted.append((f"the `{name}` input", name))
        if value:
            wanted.append((f"the `{name}` input's value", value))
    missing = [
        label for label, token in wanted if not _tokens(token) <= named
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

    ⛔ **A step that started counts, whether or not it concluded.** Reading the
    conclusion alone counted a run cut off mid-step as having executed nothing --
    the never-started reading, which is *the queue ate this run* about a run that
    reached a runner and ran. ⚠️ A **skipped** step concluded and ran nothing, so
    it is the one conclusion excluded by name.
    """
    what = f"the jobs of run `{run}` in `{repo}`"
    answer = _body(
        _host(["api", f"repos/{repo}/actions/runs/{run}/jobs?per_page=100"]),
        "how many steps the run's jobs executed",
        what,
    )
    jobs = answer.get("jobs")
    if isinstance(jobs, list) and not jobs:
        return None
    if not isinstance(jobs, list):
        raise port.HostUnavailable(
            f"{what} came back with something other than a job list in it, so "
            "how many steps the run's jobs executed is unestablished"
        )
    executed = 0
    for job in jobs:
        # ⛔ A shape this reader cannot walk is a **failed call**, while a list
        # the host stated empty is the count being unavailable. Returning `None`
        # for both would report precondition 3 unanswered about a body that was
        # garbage, which is a decision nobody made rather than one the host made.
        if not isinstance(job, dict):
            raise port.HostUnavailable(
                f"{what} lists a job this reader cannot walk, so how many steps "
                "the run's jobs executed is unestablished"
            )
        steps = job.get("steps")
        if isinstance(steps, list) and not steps:
            return None
        if not isinstance(steps, list):
            raise port.HostUnavailable(
                f"{what} states a job's steps as something other than a list, so "
                "how many steps the run's jobs executed is unestablished"
            )
        for step in steps:
            if not isinstance(step, dict):
                raise port.HostUnavailable(
                    f"{what} states a step this reader cannot walk, so how many "
                    "steps the run's jobs executed is unestablished"
                )
            concluded = step.get("conclusion")
            if concluded:
                executed += 1 if concluded != SKIPPED else 0
            elif step.get("status") in STARTED:
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
    group keyed on anything else is a supersession this misses, and ⚠️ **what a
    miss reads as is the reading the run would have had without it** -- which for
    a run that failed is `failed`, the one of § 2's four that is about the change,
    so a reviewer spends a fix cycle on a run a successor already retired.

    ⛔ **The tie is broken on the run's own id and never left to the timestamp
    alone.** This host states a run's creation to the second, so two runs of one
    workflow for one commit landing in the same second compared equal and the
    successor was missed -- measured. Ids are issued in order here, which is what
    makes them the second key.

    ⛔ **A candidate the host numbered nothing for is skipped rather than named.**
    Composing one anyway sent a reader to a run called `None`: the string is
    truthy, so it passes the blank-successor refusal one module over and the
    reading says *read the newer run* about a run nobody can open.
    """
    stated = host_checks.runner(_configuration())
    if not stated["stated"] or not stated["runner"].get("supersedes"):
        return None
    commit, workflow = record.get("head_sha"), record.get("workflow_id")
    created, mine = record.get("created_at"), record.get("id")
    if not commit or not workflow or not created:
        return None
    what = f"the runs of workflow `{workflow}` for `{commit}` in `{repo}`"
    answer = _body(
        _host([
            "api",
            f"repos/{repo}/actions/workflows/{workflow}/runs"
            f"?head_sha={commit}&per_page=100",
        ]),
        "whether a newer run retired this one",
        what,
    )
    listed = answer.get("workflow_runs")
    if not isinstance(listed, list):
        return None
    newer = [
        run
        for run in listed
        if isinstance(run, dict)
        and run.get("id")
        and run.get("id") != mine
        and _later(run, created, mine)
    ]
    if not newer:
        return None
    return str(max(newer, key=lambda run: (run.get("created_at") or "", run["id"]))["id"])


def _later(run: dict, created: str, mine) -> bool:
    """Whether this run was created after the one being read.

    ⛔ Second-resolution timestamps, so an equal one falls through to the id.
    """
    when = run.get("created_at") or ""
    if when != created:
        return when > created
    try:
        return int(run["id"]) > int(mine)
    except (TypeError, ValueError):
        return False


ADAPTER = port.Adapter(binder=bind, operations={
    name: _through_the_port(operation)
    for name, operation in {
        "runs_for_ref": runs_for_ref,
        "conclusion": conclusion,
        "log": log,
        "dispatch": dispatch,
    }.items()
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
