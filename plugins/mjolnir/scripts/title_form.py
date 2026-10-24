#!/usr/bin/env python3
"""What a pull request title opens with, derived once for both of its readers.

`host.pull_request_title` (§ 2) is one fact with two readers: the finishing role
**writes** a title and a host gate **refuses** one. ⛔ **So the derivation lives
here and nowhere else.** Before the facet existed, the form lived in a few lines
of a workflow file in one project and in whatever the role remembered -- two
statements of one rule, drifting in both directions, and the direction nothing
reports is the gate passing what it should refuse.

⛔ **It states no rule of its own.** Which keys the facet carries, what each one
is refused for, and what is procedure rather than configuration are
`../config/schema.md` § 2's, read through the shared reader; what this module
owns is the composition none of its readers should perform twice:

  * **The form** -- the reference, in sequence where the project admits more than
    one, then one space, then at least one further character. The arrangement is
    procedure and only the reference is configuration.
  * **The expression** a gate enforces, in the one dialect a host's own shell
    has: `grep -E`'s. ⛔ Composed from the reference rather than configured, so
    that a project changing the reference changes what the gate enforces with no
    file hand-edited.
  * **The title** the finishing role writes, for the identifiers it holds.
  * **The reading back** of a title against the form, which is how a role checks
    what it wrote rather than believing itself.

⚠️ **The placeholder is a run of digits, and that is a stated limit rather than
an assumption about trackers.** Whatever else an identifier carries is constant
for a project -- a tracker's own project key is the measured case -- and is
written into the reference literally, which is what makes one template serve
`[<number>]` and `[KEY-<number>]` alike. ⛔ **A tracker whose identifier varies
in more than its digits cannot be stated here, and is reported rather than
approximated**: a form that nearly matches is a gate refusing titles that are
correct.

Usage:
    title_form.py [--skills-root DIR]     the form, the expression a gate
                                          enforces, and an example of each
    title_form.py render --item N [--item M ...] --rest "<the rest of it>"
                                          the title this project's form asks for
    title_form.py check --title "<a title>"
                                          whether a title opens with the form
    title_form.py --self-test             assert every answer against planted
                                          forms, then report this project's own

Exit status, and ⛔ **four values rather than two**: 0 the title holds or the
report was produced, 1 the title does not hold, 2 the configuration could not be
read, 3 this project states no form at all. ⚠️ The last is § 11's rule at a
command line -- *no answer* collapsed into 0 reads as a title that passed, and
into 1 as a project whose titles are all wrong.

⚠️ **A project stating no configuration at all reaches 3 as well**, and that is
a deliberate collapse rather than an oversight: what a consumer of this command
asks is whether there is a rule to hold a title to, and there is not either way.
What separates them is the report, which names which of the two it met -- and the
unconfigured arm names the file to write, by § 7's rule that whoever invokes a
role by name is owed that answer.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import config  # noqa: E402 -- the one reader of the surface

# What the placeholder in a reference stands for, in the dialect below. ⛔ A run
# of digits and never a wildcard: a reference whose identifier were `.+` would
# match a title carrying prose where the item's number belongs, which is the
# permissive direction on the one field this whole facet exists to hold.
DIGITS = "[0-9]+"

# ⛔ The dialect is the one a host's own shell has, which is why it is named
# rather than left as "a regular expression": a gate runs `grep -E`, and an
# expression composed in another dialect is a gate that refuses what it should
# pass on the first reference carrying a brace. ⚠️ POSIX leaves a backslash
# before an ordinary character undefined, so only these are escaped and nothing
# else is touched.
METACHARACTERS = set(r".[]\()*+?{}|^$")

# What sits between two references, and between the last one and the rest of the
# title. ⛔ Procedure rather than configuration, per § 2: derived from the one
# project measured, and a separator key with one observation behind it is a facet
# invented rather than found.
#
# ⚠️ **The expression states the first of these as a quantifier rather than as a
# literal**, which is only correct while it is empty: a non-empty separator would
# have to be interleaved between the repetitions, and `(x)+` would then match a
# sequence no role can write. The arrangement being procedure, there is no value
# that can arrive here to break it -- so what holds the pair together is the
# assertion in the suite below and not a branch nothing can reach.
BETWEEN = ""
BEFORE_THE_REST = " "


def quoted(text: str) -> str:
    """`text` as a literal in the dialect above."""
    return "".join(f"\\{c}" if c in METACHARACTERS else c for c in text)


def form(configuration: config.Config) -> dict | None:
    """Everything this project states and this module derives, or None.

    `None` is the project's stated absence (§ 2) and never an empty form: a
    title here opens with no reference, so there is nothing for a gate to
    enforce and nothing for a role to render.
    """
    stated = configuration.pull_request_title()
    if stated is None:
        return None
    one = quoted(stated["reference"]).replace(quoted(config.PLACEHOLDER), DIGITS)
    # ⚠️ The group is written in both arms and the quantifier is the whole
    # difference, which is deliberate: two gate files differing by the one
    # character the configuration decided read as one form configured two ways,
    # where two unrelated shapes read as two rules.
    sequence = f"({one}){'+' if stated['repeated'] else ''}"
    return {
        **stated,
        "expression": f"^{sequence}{BEFORE_THE_REST}.+$",
        # One reference, anchored, which is what `holds` reads a title with. ⛔
        # The same derivation and not a second one: the expression above is this
        # with a quantifier and the rest of the title after it. ⚠️ It exists
        # because the two engines are not equally safe, which the comment on
        # `holds` states.
        "one": f"^{one}",
        # What the form asks for, in words, for a refusal a person has to read.
        # ⛔ Derived rather than written, so it cannot describe a form the
        # expression beside it does not enforce.
        "says": (
            ("one or more work-item references" if stated["repeated"]
             else "one work-item reference")
            + f", each written {stated['reference']!r}, then a space, then the rest"
            + " of the title"
        ),
        "example": render(configuration, [1, 2] if stated["repeated"] else [1],
                          "The rest of the title"),
    }


def render(configuration: config.Config, numbers, rest: str) -> str:
    """The title this project's form asks for, for the identifiers in hand.

    Raises `ValueError` where the project's own form cannot produce one, which
    is an answer and not a crash: a role asking for two references on a project
    whose form admits one is asking for a title its own gate would refuse.
    """
    stated = configuration.pull_request_title()
    if stated is None:
        raise ValueError(
            "this project states no `host.pull_request_title`, so a title here "
            "opens with no reference and there is nothing to render (§ 2)."
        )
    if not numbers:
        raise ValueError("a title carries at least one reference, so at least one "
                         "identifier is needed to render it.")
    if len(numbers) > 1 and not stated["repeated"]:
        raise ValueError(
            f"this project's form admits one reference and {len(numbers)} were "
            "given; `host.pull_request_title.repeated` is false, so a title "
            "carrying two is one its own gate refuses."
        )
    for number in numbers:
        if not re.fullmatch(r"[0-9]+", str(number)):
            raise ValueError(
                f"{number!r} is not a run of digits, and the reference's "
                f"`{config.PLACEHOLDER}` stands for one. An identifier carrying "
                "anything else is the limit this module reports rather than "
                "approximates."
            )
    if not rest or not rest.strip():
        raise ValueError("the rest of the title is what the reference precedes, and "
                         "a title that is references alone states nothing.")
    references = BETWEEN.join(
        stated["reference"].replace(config.PLACEHOLDER, str(number))
        for number in numbers
    )
    return references + BEFORE_THE_REST + rest.strip()


def _opens_with(found: dict, title: str) -> bool:
    """Whether `title` opens with this form, read one reference at a time.

    ⛔ **The expression a gate carries is not run through this language's own
    engine, and that is a measured defect rather than a preference.** The two
    engines accept the same language and are not equally safe: `grep -E` decides
    it without backtracking, while a reference ending in its own identifier —
    `<number>` alone is the shortest such form, and this module's suite states it
    as legitimate — makes the sequence ambiguous, and a backtracking engine then
    takes exponential time to refuse one. ⚠️ **Measured**: a title of 24 digits
    refused in 1.2 seconds, of 28 in 19, and of 40 in no time anybody waits — on
    the one call a role makes to read back a title it has just written.

    So the sequence is walked rather than matched: one reference anchored at the
    position reached, advancing, then the separator and a non-empty remainder.
    ⚠️ **What holds this to the gate is the suite's own arm comparing the two**,
    over forms including the ambiguous one, rather than the two being one call.
    """
    at, seen = 0, 0
    while True:
        matched = re.match(found["one"], title[at:])
        if not matched or matched.end() == 0:
            break
        at += matched.end()
        seen += 1
        if not found["repeated"]:
            break
    if seen == 0:
        return False
    rest = title[at:]
    return (rest.startswith(BEFORE_THE_REST)
            and len(rest) > len(BEFORE_THE_REST))


def holds(configuration: config.Config, title: str):
    """(whether this title opens with the form, the reason) -- or (None, why not).

    ⛔ `None` is *no answer* and is never folded into either verdict (§ 11): a
    project stating no form has no rule a title can fail, and a title read as
    passing on that account is a reader inventing a rule the project never
    wrote.
    """
    found = form(configuration)
    if found is None:
        return None, (
            "this project states no `host.pull_request_title`, so there is no "
            "rule to hold this title to (§ 2)."
        )
    if _opens_with(found, title):
        return True, f"the title opens with {found['says']}."
    return False, (
        f"the title does not open with {found['says']}. It states {title!r}."
    )


# --- the self-test ---------------------------------------------------------


def _a_project(tmp: str, title=None) -> config.Config:
    """A loadable configuration in a tree of its own, stating `title` or nothing.

    Built from an example rather than written here, for the reason the sibling
    consumers' fixtures are: a planted configuration the shared reader would
    refuse makes every answer below an answer about nothing.
    """
    import yaml

    with open(os.path.join(config.EXAMPLES, "github-issues.yaml"), encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    data["roots"] = {"code": ".", "code_is_own_repo": False}
    if title is None:
        data.get("host", {}).pop("pull_request_title", None)
    else:
        data.setdefault("host", {})["pull_request_title"] = title
    os.makedirs(os.path.join(tmp, ".claude"), exist_ok=True)
    with open(os.path.join(tmp, config.CONFIG_PATH), "w", encoding="utf-8") as handle:
        handle.write(yaml.safe_dump(data, allow_unicode=True))
    return config.load(tmp)


A_FORM = {
    "reference": f"[A-KEY-{config.PLACEHOLDER}]",
    "repeated": True,
    "into": ["release/*"],
}

# The same form admitting one reference, which is the arm a project closing one
# item at a time writes.
ONE_ONLY = {**A_FORM, "repeated": False}

# A form whose reference is the identifier and nothing else, which is what a
# tracker numbering its items plainly states. ⚠️ Here to assert the derivation
# does not require a bracket or a prefix it was first written against.
PLAIN = {**A_FORM, "reference": config.PLACEHOLDER}

# Titles the two engines are compared on below. ⛔ The expression this module
# derives is run by `grep -E` inside a generated gate and by Python's own engine
# in `holds`, so a title that the two read differently is a role reporting one
# thing and the gate another about one change.
BOTH_ENGINES = (
    "[A-KEY-1] The rest",
    "[A-KEY-1][A-KEY-2] The rest",
    "The rest with no reference",
    "[A-KEY-1]",
    "[A-KEY-x] The rest",
    "[A-KEY-1] and [A-KEY-2] after it",
    "x[A-KEY-1] The rest",
)

# The same comparison for the form whose reference is the identifier alone, which
# is where the sequence is ambiguous. ⛔ A form's own titles rather than the ones
# above: the list above is all refused by this form, so it would compare nothing
# but agreement on *no*.
PLAIN_TITLES = (
    "12 The rest",
    "1 2 The rest",
    "12",
    "12 ",
    "The rest with no reference",
    " 12 The rest",
    "1a The rest",
)


def _grep(expression: str, title: str):
    """Whether `grep -E` matches, or None where it did not answer.

    ⚠️ **`grep` on `PATH` is this suite's one unchecked precondition**, which is
    why the arm using this asserts that it *answered* before it compares
    anything: read as a skip, a missing `grep` turns the agreement between the
    two engines green while holding nothing.
    """
    import subprocess

    try:
        done = subprocess.run(
            ["grep", "-Eq", "-e", expression],
            input=title + "\n", capture_output=True, text=True, check=False,
        )
    except OSError:
        return None
    if done.returncode not in (0, 1):
        return None
    return done.returncode == 0


def _answers_within(root: str, title: str, *, seconds: int):
    """Whether this command refuses `title` for `root` inside `seconds`.

    `True` refused, `False` held, `None` it did not answer in time or the
    subprocess could not be started. ⛔ **A separate process, so the bound can be
    enforced by killing it**: the arm this exists for holds against an
    exponential match, and a call that never returns cannot be timed from the
    inside — measured as a self-test the host kills hours later rather than a
    red.
    """
    import subprocess

    try:
        done = subprocess.run(
            [sys.executable, os.path.abspath(__file__), "check",
             "--skills-root", root, "--title", title],
            capture_output=True, text=True, check=False, timeout=seconds,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    return {0: False, 1: True}.get(done.returncode)


def _carries_the_placeholder(source: str) -> list[str]:
    """Any string this source writes the placeholder into itself, docstrings aside.

    ⛔ Read as a tree and with the documentation excluded, for the reason the
    sibling step's directory arm is computed rather than matched: an arm that has
    to write down what it forbids finds its own prose. ⚠️ Measured as
    `source.count(...) == 0`, which failed on this module's own docstring --
    where naming the spelling is the documentation rather than a second
    statement of it.
    """
    import ast

    tree = ast.parse(source)
    documentation = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            first = node.body[0] if node.body else None
            if (isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant)
                    and isinstance(first.value.value, str)):
                documentation.add(id(first.value))
    return sorted({
        node.value for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
        and id(node) not in documentation and config.PLACEHOLDER in node.value
    })


def self_test() -> int:  # noqa: C901 -- one assertion per property, read in order
    """Assert every answer against planted forms, then report this project's own."""
    import tempfile

    failures: list[str] = []
    ran = 0

    def check(label: str, condition: bool, detail: str = "") -> None:
        nonlocal ran
        ran += 1
        print(f"  {'ok  ' if condition else 'FAIL'}  {label}"
              + (f": {detail}" if detail and not condition else ""))
        if not condition:
            failures.append(label)

    print("the facts this module reads rather than carries")
    check(
        "the reader this module loaded is the one beside it",
        os.path.dirname(os.path.abspath(config.__file__)) == HERE,
        f"imported {config.__file__}, which is not in this tree",
    )
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        own = handle.read()
    # ⛔ Computed from the reader's own constant rather than matched as text, for
    # the reason the sibling step's directory arm is: an arm that writes down the
    # spelling it forbids finds its own prose.
    carried = _carries_the_placeholder(own)
    check(
        "the placeholder is the reader's and not a second spelling here",
        not carried,
        f"this module writes {carried} itself, which is free to disagree with "
        "the spelling the surface declares",
    )
    check(
        "the arrangement's two halves agree: references abut, so the quantifier holds",
        BETWEEN == "",
        f"references are joined with {BETWEEN!r} and the expression states their "
        "repetition as a quantifier, which matches a sequence no role can write",
    )

    print()
    print("the form a project states, and the expression derived from it")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp, A_FORM)
        found = form(project)
        check("a stated form is read", found is not None)
        check(
            "and its expression anchors both ends",
            found["expression"].startswith("^") and found["expression"].endswith("$"),
            found["expression"],
        )
        check(
            "and admits more than one reference, which is what the project stated",
            holds(project, "[A-KEY-1][A-KEY-2] The rest")[0] is True,
            found["expression"],
        )
        check(
            "and holds the reference's own characters as literals",
            holds(project, "[A-KEY-1]X The rest")[0] is False
            and holds(project, "XA-KEY-1X The rest")[0] is False,
            found["expression"],
        )
        # ⛔ The direction the whole facet exists for: a title carrying no
        # reference, and one carrying a reference and nothing after it.
        for title in ("The rest with no reference", "[A-KEY-1]", "[A-KEY-1] ",
                      "[A-KEY-] The rest", "[A-KEY-x] The rest"):
            check(f"a title stating {title!r} does not hold",
                  holds(project, title)[0] is False, str(holds(project, title)))
        check(
            "the identifier is a run of digits and not a wildcard",
            holds(project, "[A-KEY-prose] The rest")[0] is False,
            found["expression"],
        )
        # ⚠️ A trailing reference inside the rest of the title is a title with
        # one reference and a remainder, not a second match: asserted because a
        # pattern anchored at one end only would read it as the form.
        check(
            "a reference later in the title is part of the rest",
            holds(project, "[A-KEY-1] and [A-KEY-2] after it")[0] is True,
            found["expression"],
        )

    print()
    print("a project admitting one reference refuses what one admitting many takes")
    with tempfile.TemporaryDirectory() as tmp:
        single = _a_project(tmp, ONE_ONLY)
        expression = form(single)["expression"]
        check("one reference holds", holds(single, "[A-KEY-1] The rest")[0] is True)
        check(
            "two do not, which is the configured difference rather than a second shape",
            holds(single, "[A-KEY-1][A-KEY-2] The rest")[0] is False,
            expression,
        )
        # ⛔ The acceptance this item was filed on: the enforced form changes with
        # the configuration and with nothing else. ⚠️ Asserted as an inequality of
        # the two expressions and not of their reports, a report being a sentence
        # either of them could carry.
        with tempfile.TemporaryDirectory() as other:
            many = _a_project(other, A_FORM)
            check(
                "changing the stated form changes what is enforced",
                form(many)["expression"] != expression,
                "the two forms derive one expression, so a project editing the "
                "facet would change nothing a gate does",
            )
        with tempfile.TemporaryDirectory() as other:
            plain = _a_project(other, PLAIN)
            check(
                "a reference that is the identifier alone derives a form too",
                holds(plain, "12 The rest")[0] is True
                and holds(plain, "The rest")[0] is False,
                form(plain)["expression"],
            )
            # ⛔ The form above is the shortest one whose sequence is **ambiguous**
            # — a reference ending in its own identifier — and that is where a
            # backtracking engine goes exponential. ⚠️ Measured on the expression
            # run through this language's own engine: 24 digits refused in 1.2
            # seconds, 28 in 19, and 40 in no time anybody waits. The walk is
            # what makes it linear.
            #
            # ⛔ **Bounded by killing the call and not by timing it**, which is
            # the correction this arm was written twice for: the first form
            # measured the elapsed time *after* the call, and the call it was
            # written against never returns — so the plant produced a run the
            # host kills hours later rather than a red. A hang is not a verdict.
            refused = _answers_within(plain.skills_root, "9" * 40, seconds=20)
            check(
                "and a title no reference can match is refused rather than hung over",
                refused is True,
                f"answered {refused!r}; the sequence is ambiguous here, so a title "
                "read by backtracking is a role that never returns from reading "
                "back what it wrote",
            )

    print()
    print("the title a role writes, and the reading back of it")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp, A_FORM)
        written = render(project, [48], "A title")
        check("a title is rendered from the identifier in hand",
              written == "[A-KEY-48] A title", written)
        check("and the form it was rendered from accepts it",
              holds(project, written)[0] is True, str(holds(project, written)))
        two = render(project, [48, 51], "A title")
        check("two identifiers render in sequence", two == "[A-KEY-48][A-KEY-51] A title", two)
        check("and that title holds too", holds(project, two)[0] is True, str(holds(project, two)))
        for numbers, rest, why in (
            ([], "A title", "no identifier"),
            ([48], "   ", "a title that is references alone"),
            (["forty-eight"], "A title", "an identifier that is not digits"),
        ):
            try:
                render(project, numbers, rest)
                refused = False
            except ValueError:
                refused = True
            check(f"rendering is refused for {why}", refused)
    with tempfile.TemporaryDirectory() as tmp:
        single = _a_project(tmp, ONE_ONLY)
        try:
            render(single, [48, 51], "A title")
            refused = False
        except ValueError:
            refused = True
        check("and for two identifiers on a project whose form admits one", refused)

    print()
    print("the gate's engine and this module's walk decide the same titles")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp, A_FORM)
        answered = _grep(form(project)["expression"], BOTH_ENGINES[0])
        check(
            "grep answered, which is this suite's one unchecked precondition",
            answered is not None,
            "grep did not answer, so the agreement below would be asserted "
            "against nothing; grep on PATH is what this arm needs",
        )
    if answered is not None:
        # ⛔ Every form, not the one this arm was first written against: what the
        # walk and the expression have to agree on is a *language*, and the
        # ambiguous form below is the one where they could most easily part.
        for label, stated, titles in (
            ("admitting many", A_FORM, BOTH_ENGINES),
            ("admitting one", ONE_ONLY, BOTH_ENGINES),
            ("the identifier alone", PLAIN, PLAIN_TITLES),
        ):
            with tempfile.TemporaryDirectory() as tmp:
                found = form(_a_project(tmp, stated))
                disagreed = [
                    title for title in titles
                    if _grep(found["expression"], title) != _opens_with(found, title)
                ]
                check(
                    f"a form {label}: the two agree on every title",
                    not disagreed,
                    f"they disagree on {disagreed}, which is the gate refusing what "
                    "a role reports as holding, or the reverse",
                )

    print()
    print("a project stating no form has no answer, which is not a pass")
    with tempfile.TemporaryDirectory() as tmp:
        silent = _a_project(tmp)
        check("the form is the stated absence", form(silent) is None)
        verdict, why = holds(silent, "Any title at all")
        check("and a title gets no answer rather than a verdict", verdict is None, str(verdict))
        check("named rather than omitted", "states no" in why, why)
        # ⛔ Both directions, because the failure is symmetrical: read as a pass a
        # title nobody checked reports green, and read as a refusal every title
        # such a project ever wrote is wrong.
        check("which is neither of the two verdicts", verdict is not True and verdict is not False)
        try:
            render(silent, [48], "A title")
            refused = False
        except ValueError:
            refused = True
        check("and nothing is rendered for it", refused)

    print()
    print("the command line answers with four statuses rather than two")
    with tempfile.TemporaryDirectory() as tmp:
        project = _a_project(tmp, A_FORM)
        root = project.skills_root
        check("a report exits zero", main(["--skills-root", root]) == 0)
        check("a title that holds exits zero",
              main(["check", "--skills-root", root, "--title", "[A-KEY-1] A title"]) == 0)
        check("a title that does not exits one",
              main(["check", "--skills-root", root, "--title", "A title"]) == 1)
        check("rendering exits zero",
              main(["render", "--skills-root", root, "--item", "48", "--rest", "A title"]) == 0)
        check("and a render its own form refuses exits one",
              main(["render", "--skills-root", root, "--item", "x", "--rest", "A title"]) == 1)
    with tempfile.TemporaryDirectory() as tmp:
        silent = _a_project(tmp)
        check(
            "a project stating no form exits three rather than zero or one",
            main(["check", "--skills-root", silent.skills_root, "--title", "A title"]) == 3,
            "no answer collapsed into either verdict is a title read as passing "
            "or a project read as always wrong",
        )
    with tempfile.TemporaryDirectory() as tmp:
        # ⛔ The fourth status, asserted rather than claimed. ⚠️ A configuration
        # that is there and does not load is the project's own facts badly
        # written, which is a different answer from a project that states none —
        # and both are different from a title that failed.
        os.makedirs(os.path.join(tmp, ".claude"), exist_ok=True)
        with open(os.path.join(tmp, config.CONFIG_PATH), "w", encoding="utf-8") as handle:
            handle.write("host: [this is not a block of keys\n")
        check(
            "a configuration that will not load exits two rather than three",
            main(["check", "--skills-root", tmp, "--title", "A title"]) == 2,
            "a file that is there and does not resolve is not a project stating "
            "nothing, and reported as one it reads as a decision somebody made",
        )
    with tempfile.TemporaryDirectory() as tmp:
        check(
            "and a project stating no configuration at all exits three, with the file named",
            main(["--skills-root", tmp]) == NO_FORM,
            "whoever invoked this by name is owed the answer that the project "
            "states nothing, which § 7 makes an invitation rather than silence",
        )

    print()
    print("this project's own form, read rather than assumed")
    live = config.load(config.REPO_ROOT)
    # ⛔ Stated as an equivalence rather than as *no form is stated*, so the arm
    # keeps holding if this project ever states one.
    check(
        "an absent form is named rather than read as a rule",
        (form(live) is None) == (live.get("host.pull_request_title") is None),
        "the derivation and the facet disagree about whether this project states "
        "a title form",
    )

    print()
    check(
        "this run executed assertions rather than reporting a green nothing",
        ran > 1,
        "a suite that executes no case and exits zero is the degradation every "
        "check here is written against",
    )
    print()
    if failures:
        print(f"{len(failures)} check(s) failed:")
        for label in failures:
            print(f"  - {label}")
        return 1
    print(f"every check passed ({ran} assertions).")
    return 0


# --- the command line ------------------------------------------------------

NO_FORM = 3


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="What a pull request title opens with, for this project.",
    )
    parser.add_argument("--skills-root", default=".")
    parser.add_argument("--self-test", action="store_true")
    sub = parser.add_subparsers(dest="what")

    rendering = sub.add_parser("render", help="the title this project's form asks for")
    rendering.add_argument("--skills-root", default=".")
    rendering.add_argument("--item", action="append", default=[],
                           help="one work item's identifier; repeat for a title closing several")
    rendering.add_argument("--rest", required=True, help="the rest of the title")

    reading = sub.add_parser("check", help="whether a title opens with the form")
    reading.add_argument("--skills-root", default=".")
    reading.add_argument("--title", required=True)

    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()

    # ⛔ Asked before the configuration is loaded and answered rather than
    # refused, per § 7: whoever invoked this by name is owed the answer that the
    # project states nothing.
    if not config.configured(args.skills_root):
        print(json.dumps({
            "form": None,
            "report": [
                "This project states no configuration, so nothing is known about "
                "its pull request titles. Write `.claude/mjolnir.yaml`; the keys "
                "are stated in the configuration surface shipped with the toolkit."
            ],
        }, indent=2, ensure_ascii=False))
        return NO_FORM

    try:
        configuration = config.load(args.skills_root)
    except (config.ConfigError, OSError) as exc:
        print(exc, file=sys.stderr)
        return 2

    found = form(configuration)
    if args.what == "check":
        verdict, why = holds(configuration, args.title)
        print(json.dumps({"holds": verdict, "because": why, "form": found},
                         indent=2, ensure_ascii=False))
        return NO_FORM if verdict is None else (0 if verdict else 1)

    if args.what == "render":
        try:
            title = render(configuration, args.item, args.rest)
        except ValueError as exc:
            print(json.dumps({"title": None, "because": str(exc), "form": found},
                             indent=2, ensure_ascii=False))
            return NO_FORM if found is None else 1
        print(json.dumps({"title": title, "form": found}, indent=2, ensure_ascii=False))
        return 0

    report = [] if found is not None else [
        "This project states no `host.pull_request_title`, so a title here opens "
        "with no work-item reference: the finishing role renders none, no title "
        "gate is installed, and nothing holds a title to anything (§ 2)."
    ]
    print(json.dumps({"form": found, "report": report}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
