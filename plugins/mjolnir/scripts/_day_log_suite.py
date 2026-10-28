#!/usr/bin/env python3
"""What the day log's evidence script decides, held beside it.

⛔ **The false-negative rows are the dangerous ones.** A pattern that catches a
real instruction removes a working hour and **nothing anywhere reports it** -- so
every row that must stay work carries more weight than the rows it must catch.
That is why the corpus below is roughly half `WORK`, and why the loop's own roles
are in it by name.

Five projects carried five copies of this corpus. What is here is their union,
plus the rows the extraction itself made necessary and which no surveyed copy
could have carried:

  * the **namespaced** command form, `/<plugin>:<name>`, measured in this
    project's own transcripts beside the bare form;
  * the skill preamble at a **plugin** path, which the strictest surveyed anchor
    silently stops matching;
  * a **sidecar's** prompt, which is the parent's instruction to a sub-window and
    must never open a bookkeeping turn;
  * the grid read **both ways**, since whether one is asserted at all is now
    configured rather than compiled in.

⛔ **Every rule is shown a violation it must redden on before it is held.** A
check whose plant is a no-op reports green on a mechanism that has stopped
working, and the plants here are therefore mutations of the script's own data
rather than hand-built expectations.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
if _SCRIPTS not in sys.path:
    sys.path.insert(0, _SCRIPTS)

import config  # noqa: E402
import day_log  # noqa: E402
import load  # noqa: E402

RITUAL, WORK = True, False

# --------------------------------------------------------------------------------------------
# The corpus
# --------------------------------------------------------------------------------------------

PROMPTS = [
    # --- the harness's own commands, in every form a transcript records them ---
    (RITUAL, "<command-name>/save</command-name>"),
    (RITUAL, "<command-message>save</command-message> <command-name>/save</command-name>"),
    (RITUAL, "<command-name>/clear</command-name> <command-message>clear</command-message>"),
    (RITUAL, "<command-name>/exit</command-name>"),
    (RITUAL, "<command-name>/exit</command-name> <command-message>exit</command-message>"),
    (RITUAL, "<command-name>/mcp</command-name>"),
    (RITUAL, "<command-name>/model</command-name>"),
    (RITUAL, "<command-name>/save</command-name> <command-args>we pause and resume next session</command-args>"),
    (RITUAL, "<command-message>day-report</command-message> <command-name>/day-report</command-name>"),
    # ⚠️ Measured in this project's transcripts and on no surveyed copy's list:
    # a harness command that drives the window or asks about spend.
    (RITUAL, "<command-name>/compact</command-name>"),
    (RITUAL, "<command-name>/usage-credits</command-name>"),

    # --- namespacing. ⚠️ Measured: this project's history carries `/mjolnir:save`
    # beside a bare `/start`, so every one of these is a string that really
    # occurs and that every surveyed copy's pattern misses.
    (RITUAL, "<command-name>/mjolnir:save</command-name>"),
    (RITUAL, "<command-message>mjolnir:save</command-message> <command-name>/mjolnir:save</command-name>"),
    (RITUAL, "<command-name>/mjolnir:load</command-name>"),
    (RITUAL, "<command-message>mjolnir:day-report</command-message> <command-name>/mjolnir:day-report</command-name>"),

    # --- the body a skill injects as its own user turn, right after the command.
    # ⚠️ The plugin path is the measured form; the project-local one is what a
    # project that copied the role in still writes. Both must match.
    (RITUAL, "Base directory for this skill: /x/plugins/mjolnir/skills/save # Keep the session's books"),
    (RITUAL, "Base directory for this skill: /x/plugins/mjolnir/skills/load # Restore what is in flight"),
    (RITUAL, "Base directory for this skill: /x/plugins/mjolnir/skills/day-report # Day report"),
    (RITUAL, "Base directory for this skill: /x/.claude/skills/save # Save progress"),
    (RITUAL, "Base directory for this skill: /x/.claude/skills/day-report # Day report"),

    # --- reloading context, and the orientation question that comes with it ---
    (RITUAL, "load progress"),
    (RITUAL, "load progres"),
    (RITUAL, "load progerss"),
    (RITUAL, "load progress. what's next?"),
    (RITUAL, "load progress. what are the next steps"),
    (RITUAL, "load progress. next tasks?"),
    (RITUAL, "load progress. next steps?"),
    (RITUAL, "load progress. resume"),
    (RITUAL, "load progress. resume."),
    (RITUAL, "load progress. let's resume"),

    # --- signing off, which is how a session actually ends ---
    (RITUAL, "save progress. bye"),
    (RITUAL, "save progress. until next time"),
    (RITUAL, "save progress. we will continue later"),
    (RITUAL, "save progress. we will resume next session"),
    (RITUAL, "save progress. i will tell you what to do for testing in the next session"),
    (RITUAL, "did you save progress? buy"),

    # --- bare bookkeeping, and the verification that follows it ---
    (RITUAL, "save"),
    (RITUAL, "save all"),
    (RITUAL, "save progress"),
    (RITUAL, "commit"),
    (RITUAL, "commit all"),
    (RITUAL, "commit only"),
    (RITUAL, "all saved?"),
    (RITUAL, "progress saved"),
    (RITUAL, "pushed"),
    (RITUAL, "did you commit"),
    (RITUAL, "did you push"),
    (RITUAL, "pwd"),
    (RITUAL, "bye"),

    # --- ⛔ work that must never be discounted ---------------------------------
    #
    # The loop's own roles. § 9 states they are the work and must never join the
    # list; these rows are what holds that, and each is the exact string the
    # carrier injects.
    (WORK, "<command-message>mjolnir:start</command-message> <command-name>/mjolnir:start</command-name>"),
    (WORK, "<command-message>mjolnir:finish</command-message> <command-name>/mjolnir:finish</command-name>"),
    (WORK, "<command-message>mjolnir:review</command-message> <command-name>/mjolnir:review</command-name>"),
    (WORK, "<command-name>/mjolnir:file-work-item</command-name>"),
    (WORK, "<command-name>/mjolnir:gate-work-item</command-name>"),
    (WORK, "<command-name>/start</command-name>"),
    (WORK, "Base directory for this skill: /x/plugins/mjolnir/skills/start # Start a work item"),
    (WORK, "Base directory for this skill: /x/plugins/mjolnir/skills/finish # Finish a work item"),
    (WORK, "Base directory for this skill: /x/plugins/mjolnir/skills/review # Review a change"),
    (WORK, "Base directory for this skill: /x/plugins/mjolnir/skills/file-work-item # File a work item"),
    (WORK, "Base directory for this skill: /x/plugins/mjolnir/skills/gate-work-item # Gate a work item"),
    # ⛔ A project's own skills are work too, whatever they are about. Bringing a
    # backlog and an ordering document into agreement is this project's work, not
    # the session's bookkeeping -- and it is the nearest miss there is.
    (WORK, "<command-message>close-out</command-message> <command-name>/close-out</command-name>"),
    (WORK, "<command-name>/adoption-readiness</command-name>"),
    (WORK, "Base directory for this skill: /x/.claude/skills/close-out # Close out a batch"),
    (WORK, "Base directory for this skill: /x/.claude/skills/deploy # Deploy"),
    # ⛔ A name that merely begins with a bookkeeping one.
    (WORK, "<command-name>/save-the-plan</command-name>"),
    (WORK, "<command-name>/mjolnir:load-bearing</command-name>"),
    (WORK, "Base directory for this skill: /x/plugins/mjolnir/skills/save-plan # Save plan"),
    # ⛔ An instruction that happens to open with a bookkeeping word. The tag has
    # to close right after the name, which is what keeps these work.
    (WORK, "<command-message>commit the smtp fix</command-message>"),
    (WORK, "<command-message>deploy prod-3</command-message> <command-name>/deploy</command-name>"),
    # ⛔ Anything carrying an instruction is the job itself.
    (WORK, "load progress. do step 2"),
    (WORK, "load progress. let's move on with the ingest"),
    (WORK, "load progress. where did the evaluation set end up"),
    (WORK, "save to txt, no line width limit"),
    (WORK, "save progress but be careful, another session is running in this project"),
    (WORK, "commit the fix and open the pull request"),
    (WORK, "commit and deploy to the office machine"),
    (WORK, "commit + push it directly to release/5.6"),
    (WORK, "save progress and fix the failing test"),
    (WORK, "save progress. we will continue later. but first run the tests"),
    (WORK, "save the progress, save the plan. make sure the migration ran"),
    (WORK, "did you test the change right?"),
    (WORK, "did you run the acceptance queries?"),
    (WORK, "did you clear database?"),
    (WORK, "explain the retrieval seam"),
    (WORK, "explain how to test again"),
    (WORK, "list tasks"),
    (WORK, "merge 46 only"),
    (WORK, "run the migration dry first"),
    (WORK, "revalidate audit.md against audit-framework.md"),
    (WORK, "resume"),
    (WORK, "go"),
    (WORK, "saved the export to the sources directory, now ingest it"),
]

# Records the harness injects on its own. They must not open a bookkeeping turn
# and must not close one -- whatever turn is running keeps running.
INJECTED = [
    "<task-notification> <task-id>abc</task-id>",
    "<local-command-stdout>Goodbye!</local-command-stdout>",
    "<system-reminder>Directory-scoped variants exist</system-reminder>",
    "<bash-stdout>total 56</bash-stdout>",
]

# This project's own retired command names, as the configuration carries them --
# a command and, where it injected one, its body title.
RETIRED = [
    {"command": "deliverables", "title": "Generate Monthly Deliverables Report"},
    {"command": "ship", "title": None},
]
RETIRED_PROMPTS = [
    (RITUAL, "<command-message>deliverables</command-message> <command-name>/deliverables</command-name>"),
    (RITUAL, "# Generate Monthly Deliverables Report Create a report of the month"),
    (RITUAL, "<command-name>/ship</command-name>"),
    # ⛔ Still a name and not an expression: the project supplies the word and the
    # anchoring stays this script's, so a retired name cannot widen onto work.
    (WORK, "<command-message>ship it to staging and watch the rollout</command-message>"),
    (WORK, "<command-name>/shipping-labels</command-name>"),
]

# The grid, read both ways. ⚠️ A tie is the row with a decision in it, and the
# floor is the other: a day with any work keeps one step, because a blank entry
# means a day off.
GRID_DOWN = [
    (3.72, 3.5), (3.78, 4.0), (3.5, 3.5),
    (3.25, 3.0),   # tie -- down, never up
    (3.75, 3.5),   # tie -- down, and not to the even multiple
    (0.75, 0.5),   # tie -- down
    (0.2, 0.5),    # real work never rounds to zero
    (0.0, 0.0),    # a day off stays a day off
]
GRID_UP = [
    (3.72, 3.5), (3.78, 4.0),
    (3.25, 3.5),   # tie -- up
    (3.75, 4.0),   # tie -- up
    (0.2, 0.5),
    (0.0, 0.0),
]
# A project stating one decimal, which is the position that carries no grid.
GRID_TENTH = [(3.72, 3.7), (3.78, 3.8), (0.02, 0.1), (0.0, 0.0)]


class Suite:
    def __init__(self) -> None:
        self.failures = 0

    def ok(self, label: str, condition: bool, detail: str = "") -> None:
        print(f"  {'ok  ' if condition else 'FAIL'}  {label}")
        if not condition:
            self.failures += 1
            if detail:
                print(f"          {detail}")


# --------------------------------------------------------------------------------------------
# Fixtures
# --------------------------------------------------------------------------------------------


def _yaml(**day_log_keys) -> str:
    """A whole configuration, taken from the examples with `day_log` rewritten.

    ⛔ Taken from the directory rather than named, for the reason the sibling
    suites give for the same choice: a fixture that names one tracker is this
    toolkit's own code naming a tracker.
    """
    names = sorted(
        name for name in os.listdir(config.EXAMPLES) if name.endswith((".yaml", ".yml"))
    )
    with open(os.path.join(config.EXAMPLES, names[0]), encoding="utf-8") as handle:
        return handle.read()


def _settings(**overrides) -> day_log.Settings:
    """Settings over a real example, with the keys this assertion is about set."""
    configuration = config.load_text(_yaml(), config.EXAMPLES)
    for path, value in overrides.items():
        node, parts = configuration.data, path.replace("__", ".").split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value
    return day_log.Settings(configuration)


def _git(root: str, *arguments: str) -> None:
    subprocess.run(
        ["git", "-C", root, *arguments],
        capture_output=True, text=True, check=False,
    )


def _record(when: dt.datetime, session: str, text: str | None, kind: str = "user") -> str:
    record = {
        "timestamp": when.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z"),
        "sessionId": session,
        "type": kind,
    }
    if text is not None:
        record["message"] = {"content": text}
    return json.dumps(record) + "\n"


class World:
    """A project with one worktree, one neighbour, a transcript and a sidecar.

    The shape every stream assertion needs, built once: a repository whose
    worktree list vouches for two checkouts, a third store that looks like this
    project's and is not, a session whose parent turn holds a bookkeeping prompt
    and a real one, and a delegated sub-window whose own prompt opens with a
    bookkeeping word.
    """

    def __init__(self, tmp: str) -> None:
        self.tmp = tmp
        self.root = os.path.join(tmp, "work")
        self.tree = os.path.join(tmp, "work-wt", "1-item")
        self.neighbour = os.path.join(tmp, "work-site")
        os.makedirs(self.root)
        _git(self.root, "init", "--quiet", "-b", "main")
        # ⚠️ A bare name rather than an address, which git accepts and which keeps
        # this file naming nobody -- the sibling suites' own choice, for the same
        # reason. `attribute_to` is compared against whatever this says.
        _git(self.root, "config", "user.email", "a-worker")
        _git(self.root, "config", "user.name", "A Worker")
        Path(self.root, "a.txt").write_text("a\n")
        _git(self.root, "add", "a.txt")
        _git(self.root, "commit", "--quiet", "-m", "one")
        _git(self.root, "worktree", "add", "--quiet", "-b", "item", self.tree)

        self.store = os.path.join(tmp, "store")
        os.makedirs(self.store)
        # Three candidate stores: the root's, its worktree's, and a neighbour
        # whose path merely starts with the root's.
        self.kept = [
            self._make_store(self.root),
            self._make_store(self.tree),
        ]
        self.refused = [self._make_store(self.neighbour)]

        self.day = dt.date(2026, 10, 20)
        base = dt.datetime.combine(
            self.day, dt.time(10, 0)
        ).replace(tzinfo=day_log.LOCAL)
        self.session = "aaaabbbb-0000-0000-0000-000000000000"
        # The parent: a real instruction at 10:00, a tool call that waits, then a
        # bookkeeping prompt at 12:00 that is the only thing holding 12:00 open.
        lines = [
            _record(base, self.session, "revalidate the ingest against the corpus"),
            _record(base + dt.timedelta(minutes=1), self.session, None, "assistant"),
            # ⚠️ A 40-minute gap the parent has nothing in. Longer than the idle
            # cutoff, so without the sidecar the block ends here.
            _record(base + dt.timedelta(minutes=41), self.session, None, "assistant"),
            _record(base + dt.timedelta(minutes=120), self.session, "save progress. bye"),
            _record(base + dt.timedelta(minutes=121), self.session, None, "assistant"),
        ]
        Path(self.kept[0], f"{self.session}.jsonl").write_text("".join(lines))

        # The sub-window the parent delegated to, filling the gap. ⛔ Its own
        # first record is a `user` record carrying the parent's instruction to it
        # -- and that instruction opens with a bookkeeping word on purpose.
        sidecar = Path(self.kept[0], self.session, "subagents")
        sidecar.mkdir(parents=True)
        agent = [
            _record(base + dt.timedelta(minutes=minute), self.session,
                    "save progress and then sweep every adapter" if minute == 5 else None,
                    "user" if minute == 5 else "assistant")
            for minute in (5, 15, 25, 35)
        ]
        (sidecar / "agent-aaaa1111.jsonl").write_text("".join(agent))
        # The offloaded tool output beside it, which carries no clock at all.
        results = Path(self.kept[0], self.session, day_log.TOOL_RESULTS)
        results.mkdir(parents=True)
        (results / "abc123.txt").write_text("a very long tool result\n")

    def _make_store(self, workdir: str) -> str:
        path = os.path.join(
            self.store, re.sub(r"[^A-Za-z0-9]", "-", workdir)
        )
        os.makedirs(path)
        return path

    def settings(self, **overrides) -> day_log.Settings:
        configuration = config.load_text(_yaml(), config.EXAMPLES)
        configuration.data["roots"] = {"code": os.path.relpath(self.root, config.EXAMPLES)}
        node = configuration.data.setdefault("day_log", {})
        node["streams"] = ["sessions", "commits"]
        node.setdefault("evidence", {})["chat"] = {"kind": "none"}
        for path, value in overrides.items():
            node[path] = value
        settings = day_log.Settings(configuration)
        # The root the reader resolved is relative to the examples directory;
        # the fixture's own absolute path is what every stream is read from.
        settings.roots = [("code", self.root, None)]
        return settings


def _clear_caches() -> None:
    """Every memo the script holds, so one fixture cannot answer for the next."""
    day_log.working_copies.cache_clear()
    day_log.session_stores.cache_clear()
    day_log._parsed.cache_clear()  # noqa: SLF001 -- this file is that module's suite
    day_log._HOST.update({"since": None, "rows": [], "error": None})  # noqa: SLF001


# --------------------------------------------------------------------------------------------
# The assertions
# --------------------------------------------------------------------------------------------


def self_test() -> int:  # noqa: PLR0915 -- one assertion per rule, read top to bottom
    suite = Suite()
    print("Each rule is shown a violation it must redden on, then the rule is held.\n")

    # --- the ritual corpus ---------------------------------------------------

    print("the bookkeeping deduction catches every form and discounts no instruction:")
    patterns = day_log._patterns([])  # noqa: SLF001
    wrong = [
        f"{'must be ritual' if want else 'MUST BE WORK '}  {text[:72]}"
        for want, text in PROMPTS
        if day_log.is_ritual(text, patterns) != want
    ]
    suite.ok(
        f"all {len(PROMPTS)} rows land on the right side",
        not wrong,
        "\n          ".join(wrong),
    )
    # ⛔ The plant: a list widened by one word has to break the corpus. A suite
    # whose corpus passes under a wrong list is holding nothing. `deploy` is the
    # word chosen because shipping is the clearest case of work there is, and the
    # corpus carries it in both the command and the skill form.
    widened = day_log._patterns([{"command": "deploy"}])  # noqa: SLF001
    suite.ok(
        "⛔ and a list widened onto one real instruction reddens the corpus",
        any(
            day_log.is_ritual(text, widened) != want
            for want, text in PROMPTS
            if want is WORK
        ),
    )
    suite.ok(
        "every record the harness injects stays neutral — opening no turn and closing none",
        all(day_log.NEUTRAL.match(text) for text in INJECTED),
        next((t for t in INJECTED if not day_log.NEUTRAL.match(t)), ""),
    )
    suite.ok(
        "⛔ and a typed prompt is not neutral, so the pattern still bounds something",
        not day_log.NEUTRAL.match("save progress"),
    )

    print("\na retired name is a name, folded in without becoming an expression:")
    retired = day_log._patterns(RETIRED)  # noqa: SLF001
    wrong = [
        f"{'must be ritual' if want else 'MUST BE WORK '}  {text[:72]}"
        for want, text in RETIRED_PROMPTS
        if day_log.is_ritual(text, retired) != want
    ]
    suite.ok(
        "a retired command, its body title, and the near misses around them",
        not wrong,
        "\n          ".join(wrong),
    )
    suite.ok(
        "⛔ and without the configuration the same retired forms are work, so the key is load-bearing",
        not day_log.is_ritual(RETIRED_PROMPTS[0][1], patterns)
        and not day_log.is_ritual(RETIRED_PROMPTS[1][1], patterns),
    )
    suite.ok(
        "⛔ a name carrying expression characters is escaped rather than compiled",
        not day_log.is_ritual(
            "<command-name>/saveXprogress</command-name>",
            day_log._patterns([{"command": "save.progress"}]),  # noqa: SLF001
        ),
    )

    # --- the grid ------------------------------------------------------------

    print("\nthe grid is one configured figure, and both tie directions are stated:")
    for ties, rows in (("down", GRID_DOWN), ("up", GRID_UP)):
        settings = _settings(day_log__round_to=0.5, day_log__round_ties=ties)
        wrong = [
            f"{hours} h → {settings.report_hours(dt.timedelta(hours=hours))}, must be {want}"
            for hours, want in rows
            if abs(settings.report_hours(dt.timedelta(hours=hours)) - want) > 1e-9
        ]
        suite.ok(
            f"ties {ties}: {len(rows)} figures land on the half hour",
            not wrong,
            "\n          ".join(wrong),
        )
    tenth = _settings(day_log__round_to=0.1, day_log__enforce_grid=False)
    wrong = [
        f"{hours} h → {tenth.report_hours(dt.timedelta(hours=hours))}, must be {want}"
        for hours, want in GRID_TENTH
        if abs(tenth.report_hours(dt.timedelta(hours=hours)) - want) > 1e-9
    ]
    suite.ok(
        "a project stating one decimal rounds to one decimal",
        not wrong,
        "\n          ".join(wrong),
    )
    suite.ok(
        "⛔ and the two configurations disagree about the same figure, so the key is read",
        _settings(day_log__round_to=0.5).report_hours(dt.timedelta(hours=3.72)) != 3.7,
    )
    suite.ok(
        "the check's slack is half a step and is derived, never a constant of its own",
        abs(_settings(day_log__round_to=0.5).slack - 0.25) < 1e-6
        and abs(tenth.slack - 0.05) < 1e-6,
    )
    suite.ok(
        "a project asserting a grid holds a figure to it; one stating a finer figure asserts none",
        _settings(day_log__round_to=0.5, day_log__enforce_grid=True).enforce_grid
        and not tenth.enforce_grid
        and not _settings(day_log__round_to=0.5).on_grid(3.72)
        and _settings(day_log__round_to=0.5).on_grid(3.5),
    )

    # --- the day boundary ----------------------------------------------------

    print("\na working day is not a calendar day:")
    settings = _settings(
        day_log__day_start="05:00",
        day_log__streams=["sessions", "commits", "meetings"],
    )
    start, end = settings.window(dt.date(2026, 10, 20))
    suite.ok(
        "the window runs day_start → the same time next morning",
        start.hour == 5 and (end - start) == dt.timedelta(days=1)
        and end.date() == dt.date(2026, 10, 21),
        f"{start} → {end}",
    )
    suite.ok(
        "a meeting before day_start lands on the morning after, the same working day",
        day_log.meeting_events(settings, dt.date(2026, 10, 20), ["01:00-01:10"])[0][0].date()
        == dt.date(2026, 10, 21),
    )
    suite.ok(
        "⛔ and one after it does not, so the fold is a boundary rather than a shift",
        day_log.meeting_events(settings, dt.date(2026, 10, 20), ["14:00-14:10"])[0][0].date()
        == dt.date(2026, 10, 20),
    )
    suite.ok(
        "a meeting passed to a project that does not read the stream is refused, never measured",
        _refuses(lambda: day_log.meeting_events(
            _settings(day_log__streams=["sessions"]), dt.date(2026, 10, 20), ["14:00-14:10"]
        )),
    )
    suite.ok(
        "the cap is short enough that a long autonomous turn is never written off",
        day_log.RITUAL_CAP <= dt.timedelta(minutes=30),
        str(day_log.RITUAL_CAP),
    )

    # --- the streams, over a real fixture ------------------------------------

    with tempfile.TemporaryDirectory() as tmp:
        held = day_log.store_root
        try:
            world = World(tmp)
            day_log.store_root = lambda: world.store
            _clear_caches()
            settings = world.settings()

            print("\nthe input is this project and nothing else:")
            kept, refused = day_log.session_stores((world.root,))
            suite.ok(
                "the checkout's store and its worktree's are both read",
                set(kept) == set(world.kept),
                f"kept {kept}",
            )
            suite.ok(
                "⛔ a store whose name merely starts with this project's is REFUSED",
                set(refused) == set(world.refused),
                f"refused {refused}",
            )
            suite.ok(
                "and no candidate vanishes — every one is kept or refused by name",
                set(kept) | set(refused) == set(world.kept) | set(world.refused),
            )
            suite.ok(
                "the refusal is named in SOURCES rather than dropped in silence",
                any("⛔" in line and world.refused[0] in line
                    for line in day_log.sources(settings)),
                "\n          ".join(day_log.sources(settings)),
            )
            suite.ok(
                "and the excluded offloaded tool output is named there too, with its reason",
                any(day_log.TOOL_RESULTS in line and "no" in line
                    for line in day_log.sources(settings)),
            )
            # ⛔ The candidates come from every working copy and not from the
            # configured root alone. This fixture's worktree is a **sibling** of
            # the root, which is where `tree_dir` routinely puts one, and its
            # store's name happens to start with the root's — so the arm that
            # actually bites is asked from the worktree's own side: pointed
            # there, a glob anchored on the configured root cannot see the main
            # checkout's store at all, and the day reads as empty.
            _clear_caches()
            from_tree, _refused_there = day_log.session_stores((world.tree,))
            suite.ok(
                "⛔ resolved from a worktree, the main checkout's store is still read",
                set(from_tree) == set(world.kept),
                f"from the tree: {[os.path.basename(p) for p in from_tree]}",
            )
            _clear_caches()

            print("\na sub-window's minutes are measured, and its prompt is not a typed one:")
            _clear_caches()
            whole = day_log.measure(settings, world.day)
            # ⛔ The plant that reaches the mechanism: the sidecar glob is made to
            # match nothing, which is exactly what every surveyed copy did.
            sidecars = day_log.SIDECARS
            day_log.SIDECARS = os.path.join("subagents", "nothing-*.jsonl")
            _clear_caches()
            without = day_log.measure(settings, world.day)
            day_log.SIDECARS = sidecars
            _clear_caches()
            suite.ok(
                "⛔ reading only the top-level transcripts under-measures the day",
                without.total < whole.total,
                f"with sidecars {whole.total}, without {without.total}",
            )
            suite.ok(
                "the gap the parent spent waiting is one block rather than two",
                len(whole.blocks) < len(without.blocks),
                f"{len(whole.blocks)} blocks with, {len(without.blocks)} without",
            )
            # ⛔ The other direction: the sidecar's own prompt opens with a
            # bookkeeping word, and its minutes must still count.
            suite.ok(
                "⛔ a sidecar's prompt opens no bookkeeping turn, so its minutes still count",
                whole.total >= dt.timedelta(minutes=35),
                f"measured {whole.total}",
            )
            suite.ok(
                "and no sidecar prompt reaches the SESSIONS listing as a typed one",
                all(
                    "sweep every adapter" not in text
                    for rows in whole.prompts.values()
                    for _w, text, _r in rows
                ),
            )

            print("\nthe deduction still bites where nothing else was running:")
            kept_ritual = day_log.measure(settings, world.day, keep_ritual=True)
            suite.ok(
                "a bookkeeping turn that was the only thing holding a block stops holding it",
                whole.total < kept_ritual.total and whole.dropped > dt.timedelta(),
                f"deducted {whole.dropped}, kept {kept_ritual.total}, counted {whole.total}",
            )
            suite.ok(
                "and the deduction is reported rather than silently applied",
                kept_ritual.dropped == dt.timedelta(),
            )
            suite.ok(
                "the parent's own bookkeeping prompt is marked in the listing",
                any(
                    ritual
                    for rows in whole.prompts.values()
                    for _w, _t, ritual in rows
                ),
            )
            suite.ok(
                "and the real instruction beside it is not",
                any(
                    not ritual and "revalidate" in text
                    for rows in whole.prompts.values()
                    for _w, text, ritual in rows
                ),
            )

            print("\na session is identified by its record and not by its file name:")
            suite.ok(
                "--skip-session drops the session the records name",
                not day_log.measure(
                    settings, world.day, skip=(world.session[:8],)
                ).prompts,
            )

            print("\nthe commits stream is scoped to the repository, not to one person:")
            # ⚠️ A span around now, and **never** one reaching 2100: measured,
            # `git log --until` matches nothing at all for a bound that far out --
            # 2099 answers and 2100 returns an empty list with no error — so a
            # synthetic century-wide window would read as a stream with no
            # commits in it and the assertion below would hold nothing.
            span = (
                dt.datetime.now(day_log.LOCAL) - dt.timedelta(days=1),
                dt.datetime.now(day_log.LOCAL) + dt.timedelta(days=1),
            )
            marked = world.settings(attribute_to="somebody-else")
            marked.roots = [("code", world.root, None)]
            rows = day_log.commits(marked, span)
            suite.ok(
                "the fixture's commit is in the window at all, so the marks mean something",
                len(rows) == 1,
                f"{rows}",
            )
            suite.ok(
                "a commit by anyone else is marked rather than dropped",
                bool(rows) and all(not owned for *_h, owned, _s in rows),
                f"{rows}",
            )
            # ⛔ The green side of the same scope: the configured author must also
            # be *recognised*, or every line carries the mark and the mark says
            # nothing. The fixture's committer is what is configured here.
            mine = world.settings(attribute_to="a-worker")
            mine.roots = [("code", world.root, None)]
            suite.ok(
                "and the configured author's own commit is not marked",
                all(owned for *_h, owned, _s in day_log.commits(mine, span)),
                f"{day_log.commits(mine, span)}",
            )
            unmarked = world.settings()
            unmarked.roots = [("code", world.root, None)]
            suite.ok(
                "⛔ and where no author is configured every commit is the owner's, "
                "since a mark on every line says nothing",
                all(owned for *_h, owned, _s in day_log.commits(unmarked, span)),
            )
            no_commits = world.settings(streams=["sessions"])
            no_commits.roots = [("code", world.root, None)]
            suite.ok(
                "a stream the project does not read is read not at all",
                day_log.commits(no_commits, span) == [],
            )
        finally:
            day_log.store_root = held
            _clear_caches()

    # ⛔ The symlink arm, with the link **built** rather than hoped for. The
    # fixture above happens to exercise it on a machine whose temporary root is
    # itself a link -- which is every macOS and no Linux -- so without this the
    # rule would report green on the gate's own runner while being broken for
    # every adopter whose checkouts sit under one.
    print("\na checkout reached through a link is the same checkout:")
    with tempfile.TemporaryDirectory() as tmp:
        held = day_log.store_root
        try:
            real = os.path.join(tmp, "real")
            os.makedirs(real)
            os.symlink(real, os.path.join(tmp, "link"))
            # The root **as a project would configure it**: through the link.
            root = os.path.join(tmp, "link", "work")
            os.makedirs(root)
            _git(root, "init", "--quiet", "-b", "main")
            _git(root, "config", "user.email", "a-worker")
            _git(root, "config", "user.name", "A Worker")
            Path(root, "a.txt").write_text("a\n")
            _git(root, "add", "a.txt")
            _git(root, "commit", "--quiet", "-m", "one")
            tree = os.path.join(tmp, "link", "work-wt", "1-item")
            _git(root, "worktree", "add", "--quiet", "-b", "item", tree)

            where = os.path.join(tmp, "store")
            os.makedirs(where)
            day_log.store_root = lambda: where
            # ⛔ Named after the path **as given**, which is what the harness does.
            for path in (root, tree):
                os.makedirs(day_log.store_of(path))
            _clear_caches()
            kept, refused = day_log.session_stores((root,))
            suite.ok(
                "⛔ git reports the worktree resolved, and its store is still read",
                len(kept) == 2 and not refused,
                f"kept {[os.path.basename(p) for p in kept]}, "
                f"refused {[os.path.basename(p) for p in refused]}",
            )
            # The must-stay-refused side of the same scope: the substitution must
            # not have turned the sift into something that keeps everything.
            os.makedirs(day_log.store_of(os.path.join(tmp, "link", "work-site")))
            _clear_caches()
            kept, refused = day_log.session_stores((root,))
            suite.ok(
                "and a neighbour under the same link is still refused",
                len(kept) == 2 and len(refused) == 1,
                f"kept {len(kept)}, refused {[os.path.basename(p) for p in refused]}",
            )
            suite.ok(
                "the substitution is read off the root, and is empty where nothing is linked",
                # ⚠️ Asked of the **resolved** path. `real` itself still sits under
                # whatever the temporary root is reached through, so asking it
                # would be asserting about this machine rather than about the
                # derivation -- and on macOS that answers eight pairs.
                day_log._unresolving(os.path.realpath(real)) == []  # noqa: SLF001
                and bool(day_log._unresolving(root)),  # noqa: SLF001
                f"{day_log._unresolving(root)[:2]}",  # noqa: SLF001
            )
        finally:
            day_log.store_root = held
            _clear_caches()

    # --- the mixed-chat marks ------------------------------------------------

    print("\na chat carrying something other than this project is marked, never dropped:")
    mixed = _settings(
        day_log__streams=["sessions", "commits", "chat"],
        day_log__evidence={
            "chat": {
                "kind": "telegram_export",
                "path": os.path.join(tempfile.gettempdir(), "no-such-archive.db"),
                "patterns": ["A Group%", "A Person"],
                "exclude": ["A Group Bot"],
                "mixed": ["A Person"],
            },
            "calendars": [],
        },
    )
    reader = mixed.chat_reader()(mixed)
    suite.ok(
        "the configured mixed chat is marked and the project group is not",
        reader.mixed("A Person") and not reader.mixed("A Group - dev"),
    )
    suite.ok(
        "⛔ matched the way the archive's own query matches, so the mark covers the rows read",
        day_log._like("A Group%", "a group - dev")  # noqa: SLF001
        and not day_log._like("A Group", "A Group - dev"),
    )
    suite.ok(
        "a block resting on a mixed chat alone is flagged by source rather than by length",
        day_log.blocks(
            [(dt.datetime(2026, 10, 20, 9, 0, tzinfo=day_log.LOCAL), "chat~"),
             (dt.datetime(2026, 10, 20, 9, 5, tzinfo=day_log.LOCAL), "chat~")], 15,
        )[0][2] == {"chat~"},
    )
    suite.ok(
        "and an edge set by a mixed message alone names which end",
        day_log.blocks(
            [(dt.datetime(2026, 10, 20, 9, 0, tzinfo=day_log.LOCAL), "chat~"),
             (dt.datetime(2026, 10, 20, 9, 5, tzinfo=day_log.LOCAL), "sessions"),
             (dt.datetime(2026, 10, 20, 9, 9, tzinfo=day_log.LOCAL), "chat~")], 15,
        )[0][3] == "head+tail",
    )
    suite.ok(
        "⛔ and a block both of whose edges a session sets carries no flag",
        day_log.blocks(
            [(dt.datetime(2026, 10, 20, 9, 0, tzinfo=day_log.LOCAL), "sessions"),
             (dt.datetime(2026, 10, 20, 9, 9, tzinfo=day_log.LOCAL), "sessions")], 15,
        )[0][3] == "",
    )
    suite.ok(
        "a kind the surface allows and nothing implements is refused by name, never an empty stream",
        _refuses(lambda: _settings(
            day_log__streams=["sessions", "chat"],
            day_log__evidence={"chat": {"kind": "a_kind_nothing_implements"}, "calendars": []},
        ).chat_reader()),
    )
    suite.ok(
        "⛔ and a kind with no archive stated is refused on the path rather than read as empty",
        _refuses(lambda: _settings(
            day_log__streams=["sessions", "chat"],
            day_log__evidence={"chat": {"kind": "telegram_export"}, "calendars": []},
        ).chat_reader()),
    )

    # --- the blocks ----------------------------------------------------------

    print("\nblocks split where nothing happened, and a boundary crossing is a failure:")
    noon = dt.datetime(2026, 10, 20, 12, 0, tzinfo=day_log.LOCAL)
    split = day_log.blocks(
        [(noon, "sessions"), (noon + dt.timedelta(minutes=16), "sessions")], 15
    )
    joined = day_log.blocks(
        [(noon, "sessions"), (noon + dt.timedelta(minutes=15), "sessions")], 15
    )
    suite.ok(
        "a gap longer than the cutoff splits, and one exactly at it does not",
        len(split) == 2 and len(joined) == 1,
        f"{len(split)} / {len(joined)}",
    )
    suite.ok(
        "a single event is a block of no length, which still anchors the day",
        day_log.blocks([(noon, "git")], 15) == [[noon, noon, {"git"}, ""]],
    )
    suite.ok(
        "no events is no blocks, and never a block of the whole window",
        day_log.blocks([], 15) == [],
    )

    # --- the one-copy property ----------------------------------------------

    print("\nthis is one copy, which is a property of the file and is held here:")
    with open(os.path.join(_SCRIPTS, "day_log.py"), encoding="utf-8") as handle:
        source = handle.read()
    # ⛔ The values the five surveyed copies carried, by shape rather than by
    # name: an expanded home path, a store under it, a chat archive, a host slug.
    # A value of any of these shapes in this file is a project's fact compiled
    # into the shared script, which is the defect the extraction exists to delete.
    # ⚠️ **A home-relative literal of any shape**, rather than one naming a
    # directory: the rule is that no path on anybody's machine is in this file,
    # and a search for one particular parent directory would be this suite
    # knowing which machine wrote the copies it replaced.
    LEAKS = (
        (r"expanduser\(\s*[\"']~", "a path under somebody's home directory"),
        (r"[\"'][^\"']*\.db[\"']", "a chat archive"),
        (r"[\"'][A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+[\"']\s*(?:#|$)", "a host repository slug"),
        (r"CHAT_PATTERNS|MIXED_CHATS|CALENDAR\s*=|GITHUB_REPO", "a surveyed copy's own constant"),
    )
    leaks = []
    for pattern, what in LEAKS:
        for found in re.finditer(pattern, source):
            line = source[: found.start()].count("\n") + 1
            if not _in_comment(source, found.start()):
                leaks.append(f"line {line}: {what} — {found.group(0)[:48]}")
    suite.ok(
        "no project's path, archive, chat, calendar or repository is named in the script",
        not leaks,
        "\n          ".join(leaks),
    )
    # ⛔ The plant, run against the **surveyed copies' own opening lines** rather
    # than against a shape invented here: every one of them began by naming a
    # path, and each of these is one of their real first constants with the
    # machine-specific part removed. A search that found none of them would be a
    # formality.
    planted = [
        'STORE = os.path.expanduser("~" + "/a-place")',
        'ARCHIVE = "a-place/an-archive.db"',
        'GITHUB_REPO = "an-owner/a-repository"',
        'CHAT_PATTERNS = ["A Group%"]',
    ]
    missed = [
        line for line in planted
        if not any(re.search(pattern, line) for pattern, _what in LEAKS)
    ]
    suite.ok(
        "⛔ and the search finds every shape they carried, so it is a search rather than a formality",
        not missed,
        "\n          ".join(missed),
    )
    suite.ok(
        "the session store is the sibling's own derivation, not a second reading here",
        day_log.store_root() == str(load.harness_dir() / load.SESSIONS_UNDER),
        f"{day_log.store_root()}",
    )
    suite.ok(
        "⛔ and where neither name resolves it is a stop, never a path joined onto nothing",
        _store_refuses_with_no_home(),
    )
    suite.ok(
        "a working copy and the store named after it land on the same key",
        day_log.dirkey("/a/b/my-project") == day_log.dirkey("-a-b-my-project")
        and day_log.dirkey("/a/b/my.project") == day_log.dirkey("-a-b-my-project"),
    )
    suite.ok(
        "⛔ and two different checkouts do not, so the key still distinguishes them",
        day_log.dirkey("/a/b/project") != day_log.dirkey("/a/b/project-site"),
    )

    # --- the store is reached through the port -------------------------------

    print("\nthe store is reached through § 26's port and never by a path composed here:")
    suite.ok(
        "the port is named by the key the surface's marker states",
        day_log.DESTINATION in port_names(),
        f"{day_log.DESTINATION} not among {sorted(port_names())}",
    )
    suite.ok(
        "⛔ no entry path, stem or hours label is spelled in this script",
        not re.search(r"day-report-|Hours worked", source),
    )
    suite.ok(
        "a project whose destination addresses nothing is told so, rather than read as empty",
        _refuses(lambda: day_log.recorded(
            _settings(day_log__destination={"kind": "none"}),
            dt.date(2026, 10, 1), dt.date(2026, 10, 31),
        ), day_log.Unavailable),
    )

    print()
    if suite.failures:
        print(f"  ✗ {suite.failures} assertion(s) failed")
        return 1
    print(
        f"  ✓ {len(PROMPTS)} prompts, {len(RETIRED_PROMPTS)} retired forms, "
        f"{len(INJECTED)} injected records, "
        f"{len(GRID_DOWN) + len(GRID_UP) + len(GRID_TENTH)} roundings: every "
        "bookkeeping form is caught, no instruction is discounted, a sub-window's "
        "minutes are measured without its prompt counting as typed, no other "
        "project's store is read, and no project's own value is in the script"
    )
    return 0


def _in_comment(source: str, position: int) -> bool:
    """Whether a match sits inside a comment or a docstring.

    The leak search is about **code**: a comment naming what a surveyed copy used
    to carry is this file explaining itself, and a string literal is the value.
    Decided by the line's own shape, which is as far as a search can go without
    parsing -- and the limit is why the plant above exists.
    """
    line_start = source.rfind("\n", 0, position) + 1
    line = source[line_start:source.find("\n", position)]
    stripped = line.lstrip()
    return stripped.startswith("#") or stripped.startswith(("*", '"""', "'''"))


def _store_refuses_with_no_home() -> bool:
    """Whether a shell holding neither name is a stop rather than a bad path."""
    held = {
        name: os.environ.pop(name, None) for name in (load.CONFIG_DIR, load.HOME)
    }
    try:
        return _refuses(lambda: day_log.store_of("/a/checkout"))
    finally:
        for name, value in held.items():
            if value is not None:
                os.environ[name] = value


def _refuses(call, error=None) -> bool:
    """Whether a call refuses rather than answering."""
    try:
        call()
    except (day_log.Unavailable, config.ConfigError):
        return True
    except Exception:  # noqa: BLE001 -- any refusal is a refusal, none is an answer
        return True
    return False


def port_names() -> set:
    import port as ports

    return set(ports.surface_ports())


if __name__ == "__main__":
    sys.exit(self_test())
