#!/usr/bin/env python3
"""The rail under the authorship rule: tool attribution out of a commit message.

`../config/schema.md` § 6 states that the only author is the code host's
authenticated user, that no tool is recorded as an author or a co-author, and
that no generated-by marker appears in a commit message. ⛔ **This module states
none of that and enforces it.** What it owns is the one question the rule leaves
open -- *which lines in a message are a tool's attribution* -- and the answer is
written here once, because a second spelling of it would be free to disagree
with the copy git actually calls.

⛔ **Below the model's control, which is the whole reason it exists.** The rule
has three possible layers and the first two both leak: an agent setting that
reports have shown is not honoured when a commit is made by a shell command
rather than through an internal commit path, and an instruction in a project's
rules file, which survives neither a compaction nor a new agent. A `commit-msg`
hook runs on every commit from any path, so it is the only one that cannot be
talked out of. ⚠️ **It is a git hook and not an agent process hook** -- a
different mechanism with a different lifecycle from the ones in `hooks.json`,
which fire on tool events in a session where this fires on `git commit` whoever
runs it.

**The address decides, never the display name.** ⛔ A `Co-Authored-By:` line is
stripped on the strength of the **address** it carries, and a display name is
read for nothing a person could have chosen. ⚠️ The reason is a measured
collision rather than taste: `Claude` is an ordinary given name, so a rule
matching the name would eat a human co-author -- which is the one outcome § 6
forbids outright, pairing credit being legitimate and the rule having only ever
excluded tools. An address is a vendor's own, and a person's is theirs.

⚠️ **One marker is read across the whole trailer, and it is the stated exception
rather than a hole in that rule**: the host's `[bot]` suffix, which it writes in
the display name as often as in the address. ⛔ **It is admissible because it is
not a name anybody chooses** -- the host reserves it for an account that is not a
person -- so it cannot collide with a human the way a product name collides with
a given name.

**What the recognition list cannot be, and the direction it fails in.** ⛔ There
is no shape that identifies a tool, so what is recognised is a **list**, and a
tool whose spelling is not on it keeps its trailer. ⚠️ That is the safe
direction and is chosen rather than met: a trailer that survives is visible in
the message to whoever reads it and is taken out by the next commit once the
list grows, while a human co-author eaten by a rule that guessed is gone from
the record and nothing reports the loss. ⛔ **So the residue is stated and never
closed by widening the match**: see the list below for what each entry is on it
for.

**Three halves of § 6 this cannot reach, named rather than left to be assumed:**

  * **The author and the committer headers.** They are not in the message, and
    no `commit-msg` hook is given them. What holds those is the host's own
    authenticated identity.
  * **A pull request body.** No git hook sees one, so the marker that goes in a
    description is the finishing role's to not write -- stated in that role,
    because a reader who found this rail would otherwise assume it covered the
    body too.
  * **Existing history.** § 6's rule binds what is written from now on, and this
    rewrites the message being written and nothing else. ⛔ It is not a licence
    to rewrite a past full of tool trailers, and a run of it over history is not
    a use this module admits.

Usage:
    strip_attribution.py <message-file>   strip the file in place; what git calls
    strip_attribution.py <message-file> --dry-run
                                          print what would come out, write
                                          nothing
    strip_attribution.py --render         the `commit-msg` hook an adopting
                                          repository gets
    strip_attribution.py --self-test      assert every arm against planted
                                          messages

Exit status: 0 the message holds no tool attribution, or holds none any more; 1
the message is **nothing but** tool attribution, so there is no message left to
commit and the file is left as it was; 2 the file could not be read or written,
which aborts the commit deliberately -- a rail that cannot read the message
cannot hold the rule, and § 11's rule that a report names what it could not
establish means it may not pass in silence.

⚠️ **A repository stating a non-UTF-8 `i18n.commitEncoding` reaches that 2 and
is told so**, the message being read as UTF-8. ⛔ Stated rather than left to be
discovered: the direction is the safe one -- the commit stops instead of
attribution passing -- but a developer meeting it needs to know it is the
encoding and not their message. ⚠️ **A repository stating a non-default
`core.commentChar`** has its comment lines counted as content by the emptiness
test, which also fails safe: this rail does not abort, and git's own cleanup then
strips the comments and aborts on the empty message itself.
"""

from __future__ import annotations

import argparse
import os
import re
import sys

# --- what the rail recognises ----------------------------------------------
#
# ⛔ Data, and every entry carries what it is on the list for. A list whose
# members state no reason is a list nobody can audit: the next reader cannot
# tell a measured spelling from a guess, and a guess here eats a person's
# credit. ⚠️ **Lower case, and compared lower case** -- an address is
# case-insensitive in its domain and the display name is read for nothing, so
# there is no arm where case carries meaning.

# Domains a vendor owns. ⛔ Matched against the **domain** of the address a
# trailer carries, whole or as a parent of it, and never as a substring of the
# line -- a bare substring test matches a domain that merely *ends* with a
# vendor's, which belongs to whoever registered it and not to the vendor.
TOOL_DOMAINS: tuple[tuple[str, str], ...] = (
    ("anthropic.com",
     "the vendor of the assistant this toolkit is driven by, and the domain in "
     "the `Co-Authored-By` trailer its harness is configured to append"),
)

# Product and vendor spellings, for the one rule that has no address to read:
# a generated-by marker is prose, so the line names a tool or it names nothing.
# ⛔ Never applied to a `Co-Authored-By:` line, where the address rule above is
# the whole test and a name is a person's own.
TOOL_NAMES: tuple[tuple[str, str], ...] = (
    ("claude code",
     "the product named in the marker this toolkit's own harness is configured "
     "to write into a pull request body"),
    ("claude.com/claude-code",
     "the link that marker carries, which survives a line whose prose was "
     "reworded"),
    ("anthropic.com",
     "the same vendor domain as above, reaching a marker that links to it "
     "rather than naming the product"),
)

# The host's own convention for an account that is not a person. ⛔ A shape and
# not a vendor name, which is what makes it the one recognition here that needs
# no list entry per tool: GitHub appends it to every bot account's login, so a
# trailer carrying it names a bot whoever wrote the bot.
BOT_MARKER = "[bot]"

# A trailer that records a co-author. ⛔ One token and not git's whole trailer
# grammar: this is the only message-side token § 6 names, the author and the
# committer being headers no hook is given. ⚠️ `Signed-off-by` is deliberately
# absent -- it is a person's attestation about a change, so a tool writing one
# is a defect in the tool rather than a line this rail quietly tidies away.
CO_AUTHOR = re.compile(r"^co-authored-by\s*:\s*(?P<value>.*?)\s*$", re.IGNORECASE)

# The address inside a trailer's value, which is what decides it.
ADDRESS = re.compile(r"<\s*(?P<address>[^<>]+?)\s*>")

# A value that is a bare address with no angle brackets, which git accepts.
BARE_ADDRESS = re.compile(r"^(?P<address>[^\s<>@]+@[^\s<>@]+)$")

# The phrase a generated-by marker is built on. ⛔ Not sufficient on its own:
# the line has to name a recognised tool as well, so that a person writing
# *generated with care* keeps their line.
GENERATED = re.compile(r"\bgenerated\s+(?:with|by)\b", re.IGNORECASE)

# What git treats as a comment in a message file. ⚠️ The default, and a
# repository stating another `core.commentChar` has its comment lines counted as
# content by the emptiness test below -- which fails in the safe direction: the
# rail does not abort, and git's own cleanup then strips the comments and aborts
# on the empty message itself.
COMMENT = "#"


def _domain(address: str) -> str | None:
    """The domain of an address, lower case, or None where there is not one."""
    if address.count("@") != 1:
        return None
    domain = address.rsplit("@", 1)[1].strip().lower()
    return domain or None


def _address_of(value: str) -> str | None:
    """The address a trailer's value carries, or None where it carries none."""
    found = ADDRESS.search(value)
    if found is not None:
        return found.group("address").strip()
    bare = BARE_ADDRESS.match(value.strip())
    return bare.group("address") if bare is not None else None


def tool_co_author(value: str) -> str | None:
    """Why this trailer value names a tool, or None where it names a person.

    ⛔ The address and the bot marker, and nothing else. ⚠️ A value carrying no
    address at all answers None: a trailer git cannot attribute is one this rail
    will not guess at either, and the direction of that is the stated one --
    a line left in rather than a person taken out.
    """
    address = _address_of(value)
    if address is None:
        return None
    # ⛔ **The one read of the whole trailer and the one exception to the rule
    # above, stated here because the code would otherwise contradict its own
    # docstring.** The host writes this marker in the **display name** as often
    # as in the address -- a bot whose address is a numeric login carries it
    # nowhere else -- so a read of the address alone loses exactly the trailers
    # this arm exists for. ⚠️ **It is not the display-name rule readmitted**:
    # `[bot]` is a suffix the host reserves for an account that is not a person,
    # not a name anybody chooses, so it cannot collide with a human the way a
    # product name collides with a given name.
    #
    # ⚠️ One condition and not two: the address is part of the value, so a
    # separate test of its local part was a second spelling of a question this
    # one already answers.
    if BOT_MARKER in value.lower():
        return (f"the trailer carries `{BOT_MARKER}`, the host's own marker for an "
                "account that is not a person")
    domain = _domain(address)
    if domain is None:
        return None
    for owned, why in TOOL_DOMAINS:
        if domain == owned or domain.endswith("." + owned):
            return f"`{domain}` is {why}"
    return None


def generated_marker(line: str) -> str | None:
    """Why this line is a generated-by marker, or None where it is not one.

    ⛔ Both halves, and the second is what keeps a person's prose. ⚠️ Measured
    against the phrase alone: *a report generated with the figures above* is an
    ordinary sentence, and a rule on the phrase would take it out of a message
    that never mentioned a tool.
    """
    if GENERATED.search(line) is None:
        return None
    lowered = line.lower()
    for name, why in TOOL_NAMES:
        if name in lowered:
            return f"a generated-by marker naming `{name}`, which is {why}"
    return None


def attribution(line: str) -> str | None:
    """Why this line is tool attribution, or None where it is not.

    ⛔ The one place a line is judged, so that the hook, the dry run and the
    suite all ask the same question of it.
    """
    trailer = CO_AUTHOR.match(line)
    if trailer is not None:
        found = tool_co_author(trailer.group("value"))
        return None if found is None else f"a co-author trailer whose {found}"
    return generated_marker(line)


def holds_content(text: str) -> bool:
    """Whether anything here would still be a commit message.

    ⚠️ Blank lines and comment lines are not content, which is what makes a
    message that was nothing but attribution answer False.
    """
    return any(
        line.strip() and not line.strip().startswith(COMMENT)
        for line in text.split("\n")
    )


def strip(text: str) -> tuple[str, list[tuple[str, str]]]:
    """`text` with every tool attribution line out of it, and what came out.

    ⛔ **Byte-identical where nothing matched**, returned as the same object's
    value rather than reassembled -- which is what makes a second run over the
    first run's output a no-op by construction instead of by argument.

    ⛔ **Every matching line, wherever it is, and never the last trailer
    block.** A squashed merge concatenates many messages, so one message
    legitimately carries several trailer blocks with human co-authors among
    them; a rule scoped to the end of the message would keep every tool trailer
    but the last.

    ⚠️ **The only whitespace touched is the trailing run of blank lines**, which
    a removed final trailer leaves behind. Blank lines the removal leaves in the
    *middle* are left exactly as they are: collapsing them is a change to the
    project's own text, and git's own cleanup already does it.
    """
    lines = text.split("\n")
    kept: list[str] = []
    out: list[tuple[str, str]] = []
    for line in lines:
        why = attribution(line)
        if why is None:
            kept.append(line)
        else:
            out.append((line, why))
    if not out:
        return text, []
    while kept and not kept[-1].strip():
        kept.pop()
    stripped = "\n".join(kept)
    if stripped and text.endswith("\n"):
        stripped += "\n"
    return stripped, out


# --- the command line ------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Take tool attribution out of a commit message as it is written.",
    )
    parser.add_argument(
        "message_file",
        help="the file holding the proposed message; git passes it as the one argument",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="print what would come out and write nothing",
    )
    # ⛔ Strict, and an unknown argument is refused rather than ignored: a hook
    # given a second argument by some path nobody measured is a hook whose
    # behaviour nobody stated, and refusing aborts the commit rather than
    # passing attribution through on a guess.
    args = parser.parse_args(argv)

    try:
        with open(args.message_file, encoding="utf-8") as handle:
            text = handle.read()
    except OSError as exc:
        print(f"the commit message could not be read, so tool attribution was not "
              f"held: {exc}", file=sys.stderr)
        return 2

    stripped, out = strip(text)

    for line, why in out:
        where = "would come out" if args.dry_run else "taken out"
        print(f"{where}: {line.strip()}\n  -- {why}", file=sys.stderr)

    if not out:
        return 0

    if not holds_content(stripped):
        print("this commit message is nothing but tool attribution, so taking it out "
              "leaves no message to commit. The message file is left as it was; write "
              "a message that says what the change does.", file=sys.stderr)
        return 1

    if args.dry_run:
        return 0

    try:
        with open(args.message_file, "w", encoding="utf-8") as handle:
            handle.write(stripped)
    except OSError as exc:
        print(f"the commit message could not be written back, so the attribution above "
              f"is still in it: {exc}", file=sys.stderr)
        return 2
    return 0


# ---- the vendored half ends here ------------------------------------------
#
# ⛔ The line above is the sentinel `render` splits on, and everything below it
# is the renderer and the suite. Nothing below states a rule about a message: a
# rule down here would be one git's own call never executes, since the copy it
# calls is the half above.


RENDER_SENTINEL = "# ---- the vendored half ends here "

# What the rendered copy ends with, in place of everything below the sentinel.
# ⛔ Nothing in it moves between runs, which is the install step's byte-identical
# property reaching this artifact.
RENDER_TAIL = 'if __name__ == "__main__":\n    sys.exit(main())\n'


def _source() -> str:
    with open(os.path.abspath(__file__), encoding="utf-8") as handle:
        return handle.read()


def render() -> str:
    """The `commit-msg` hook an adopting repository gets.

    ⛔ The half above the sentinel and not the whole file. The suite below plants
    addresses and markers of its own, and a whole-file copy would carry every one
    of them into an adopting repository -- vendor spellings in a hook whose list
    is the one thing a reader of it needs to be able to audit.

    ⛔ **Nothing is rendered in.** Unlike the body gate's checker this artifact
    reads no configured value, because § 6 makes authorship procedure rather than
    configuration: a project that could state its own recognition list would be
    stating which tools it credits.
    """
    source = _source()
    if RENDER_SENTINEL not in source:
        raise ValueError(
            f"this file states no {RENDER_SENTINEL!r} line, so there is no half to "
            "vendor. The sentinel is what a render splits on, and a file without it "
            "would ship the suite's own planted spellings into a repository."
        )
    return source.split(RENDER_SENTINEL)[0] + RENDER_TAIL


def self_test() -> int:  # noqa: C901 -- one assertion per property, read in order
    """Assert every arm against planted messages, then assert the vendored copy."""
    import ast
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

    # The spellings the arms below are written against. ⛔ Composed from the
    # list rather than written out, so an arm cannot go on passing against a
    # literal the list no longer carries.
    #
    # ⛔ **Every planted address that is not the vendor's is a single-label
    # `.invalid` one**, and the vendor's is composed rather than written. ⚠️ Not
    # cosmetic: the sibling sweep that holds this tree to naming no address
    # reddened on four literals here, one of them a real person's -- a fixture
    # is the easiest place for an identity to land and the hardest place to
    # notice one.
    domain = TOOL_DOMAINS[0][0]
    tool = f"Co-Authored-By: A Tool <noreply@{domain}>"
    bot = "Co-Authored-By: a-generator[bot] <a-generator@invalid>"
    human = "Co-Authored-By: A Person <a.person@invalid>"
    # ⚠️ The collision this rule exists for: a person whose given name is the
    # vendor's product name, with an address of their own.
    namesake = "Co-Authored-By: Claude Dubois <claude.dubois@invalid>"
    marker = "🤖 Generated with [Claude Code](https://claude.com/claude-code)"

    print("the acceptance check, one arm each")

    # 1. A message carrying a tool trailer is committed without it, and the rest
    #    of the message is unchanged byte for byte.
    before = f"Subject line\n\nA paragraph of body.\n\n{tool}\n"
    after, out = strip(before)
    check("a tool trailer comes out", after == "Subject line\n\nA paragraph of body.\n",
          repr(after))
    check("  and the reason names the address", len(out) == 1 and domain in out[0][1],
          str(out))
    check("  and the rest is unchanged byte for byte",
          after == before.replace(f"\n{tool}\n", "").rstrip("\n") + "\n", repr(after))

    # 2. A message carrying a human co-author keeps it.
    kept = f"Subject line\n\n{human}\n"
    check("a human co-author is kept", strip(kept) == (kept, []), repr(strip(kept)))
    check("  and so is a namesake of the product, on their own address",
          strip(f"Subject\n\n{namesake}\n")[1] == [],
          str(strip(f"Subject\n\n{namesake}\n")[1]))

    # 3. A squashed message with both kinds, interleaved, keeps every human one
    #    and loses every tool one.
    squashed = (
        "A squashed subject (#1)\n"
        "\n"
        "First message.\n"
        "\n"
        f"{tool}\n"
        f"{human}\n"
        "\n"
        "Second message.\n"
        "\n"
        f"{human}\n"
        f"{bot}\n"
        "\n"
        "Third message.\n"
        "\n"
        f"{marker}\n"
        f"{tool}\n"
    )
    squeezed, taken = strip(squashed)
    check("the squash case: every tool line comes out", len(taken) == 4, str(taken))
    check("  and every human line stays", squeezed.count(human) == 2, repr(squeezed))
    check("  and no tool line survives",
          tool not in squeezed and bot not in squeezed and marker not in squeezed,
          repr(squeezed))
    check("  and the bodies between them are all still there",
          all(part in squeezed
              for part in ("First message.", "Second message.", "Third message.")),
          repr(squeezed))
    # ⛔ The arm that makes *every block* load-bearing rather than incidental, and
    # it is asked of the **first** block because that is the one a scoped rule
    # keeps. ⚠️ Measured against a rule scoped to the message's last paragraph:
    # the first block kept its tool trailer beside the human one, which this arm
    # reddens on and a count over the whole message does not.
    first_block = squeezed.split("Second message.")[0]
    check("  and that is not the last block alone",
          first_block.count("Co-Authored-By") == 1, repr(first_block))

    # 4. Running the hook on its own output changes nothing.
    again, twice = strip(squeezed)
    check("idempotent: a second pass takes nothing", twice == [], str(twice))
    check("  and changes no byte", again == squeezed, repr(again))

    print()
    print("the trailing whitespace the removal must not leave behind")
    for label, text, wanted in (
        ("one trailer at the end", f"Subject\n\n{tool}\n", "Subject\n"),
        ("a trailer block at the end", f"Subject\n\n{marker}\n{tool}\n", "Subject\n"),
        ("blank lines already there", f"Subject\n\n\n\n{tool}\n", "Subject\n"),
        ("no final newline", f"Subject\n\n{tool}", "Subject"),
        ("a body after the block", f"Subject\n\n{tool}\n\nMore.\n",
         "Subject\n\n\nMore.\n"),
    ):
        check(f"trailing: {label}", strip(text)[0] == wanted, repr(strip(text)[0]))

    print()
    print("a message that is nothing but attribution is refused, not emptied")
    with tempfile.TemporaryDirectory() as tmp:
        only = os.path.join(tmp, "only-attribution")
        with open(only, "w", encoding="utf-8") as handle:
            handle.write(f"{marker}\n{tool}\n")
        status = main([only])
        with open(only, encoding="utf-8") as handle:
            left = handle.read()
        check("it exits 1", status == 1, str(status))
        check("  and the file is left exactly as it was",
              left == f"{marker}\n{tool}\n", repr(left))

        # ⚠️ Comments are not content, so a message git would clean up to nothing
        # reaches the same refusal rather than being written out as comments only.
        commented = os.path.join(tmp, "comments-only")
        with open(commented, "w", encoding="utf-8") as handle:
            handle.write(f"{tool}\n{COMMENT} Please enter a commit message.\n")
        check("  and so does one holding only comments beside it",
              main([commented]) == 1)

        print()
        print("the hook's own invocation: one argument, written in place")
        message = os.path.join(tmp, "COMMIT_EDITMSG")
        with open(message, "w", encoding="utf-8") as handle:
            handle.write(f"Subject\n\nBody.\n\n{human}\n{tool}\n")
        check("it exits 0", main([message]) == 0)
        with open(message, encoding="utf-8") as handle:
            written = handle.read()
        check("  and the file holds the stripped message",
              written == f"Subject\n\nBody.\n\n{human}\n", repr(written))
        check("  and a second call changes nothing",
              main([message]) == 0 and open(message, encoding="utf-8").read() == written)

        # ⛔ A dry run writes nothing, which is what makes it safe to point at a
        # message somebody is still editing.
        dry = os.path.join(tmp, "dry")
        with open(dry, "w", encoding="utf-8") as handle:
            handle.write(f"Subject\n\n{tool}\n")
        check("a dry run exits 0", main([dry, "--dry-run"]) == 0)
        check("  and writes nothing",
              open(dry, encoding="utf-8").read() == f"Subject\n\n{tool}\n")

        # ⛔ Unreadable is 2 and never 0: a rail that cannot read the message
        # cannot hold the rule, and passing in silence is the one answer § 11
        # refuses.
        check("a file that is not there exits 2",
              main([os.path.join(tmp, "no-such-file")]) == 2)

    print()
    print("the generated-by marker rule names a tool or keeps the line")
    for label, line, removed in (
        ("the marker this harness writes", marker, True),
        ("the same marker without its emoji",
         "Generated with [Claude Code](https://claude.com/claude-code)", True),
        ("a marker naming the vendor's domain",
         f"Generated by a tool at {domain}", True),
        ("a person's own sentence", "The table was generated with the figures above.",
         False),
        ("a sentence naming no tool", "Generated by hand over two afternoons.", False),
        ("a line about this very rule",
         "Nothing generated by a tool may be credited here.", False),
    ):
        check(f"marker: {label}", (attribution(line) is not None) is removed,
              str(attribution(line)))

    print()
    print("the address decides, and a display name decides nothing")
    for label, line, removed in (
        ("the vendor's own address", tool, True),
        ("a subdomain of it",
         f"Co-Authored-By: A Tool <noreply@mail.{domain}>", True),
        ("the host's bot marker", bot, True),
        ("a bot marker in the display name",
         "Co-Authored-By: some-app[bot] <an-app@invalid>", True),
        # ⛔ Both placements, because the host uses both and the record claims
        # both. ⚠️ The display-name arm alone was the first form of this, which
        # left the address placement asserted in the record and held by nothing.
        ("a bot marker in the address and not the name",
         "Co-Authored-By: Some App <some-app[bot]@invalid>", True),
        ("a person", human, False),
        ("a person named for the product", namesake, False),
        ("a domain that merely ends with the vendor's",
         f"Co-Authored-By: Someone <a@{domain}.elsewhere.test>", False),
        ("a domain that merely starts with it",
         f"Co-Authored-By: Someone <a@not-{domain}>", False),
        ("a trailer carrying no address at all",
         "Co-Authored-By: Claude Code", False),
        ("a lower-cased token", tool.replace("Co-Authored-By", "Co-authored-by"), True),
        ("an upper-cased token", tool.replace("Co-Authored-By", "CO-AUTHORED-BY"), True),
        ("a spaced token", tool.replace("Co-Authored-By:", "Co-Authored-By :"), True),
        ("a signed-off-by naming the vendor",
         f"Signed-off-by: A Tool <noreply@{domain}>", False),
        ("a line that merely quotes the trailer",
         f"We used to write Co-Authored-By: Claude <noreply@{domain}> here.", False),
    ):
        check(f"address: {label}", (attribution(line) is not None) is removed,
              str(attribution(line)))

    print()
    print("the recognition list is well-formed, every entry")
    for name, entries in (("TOOL_DOMAINS", TOOL_DOMAINS), ("TOOL_NAMES", TOOL_NAMES)):
        check(f"{name} is not empty", bool(entries))
        check(f"{name} states no spelling twice",
              len({spelling for spelling, _ in entries}) == len(entries),
              str([spelling for spelling, _ in entries]))
        for spelling, why in entries:
            check(f"{name}: `{spelling}` is lower case", spelling == spelling.lower())
            check(f"{name}: `{spelling}` carries no surrounding space",
                  spelling == spelling.strip() and spelling != "")
            check(f"{name}: `{spelling}` says what it is on the list for",
                  isinstance(why, str) and len(why.split()) >= 5, repr(why))
    for spelling, _why in TOOL_DOMAINS:
        check(f"TOOL_DOMAINS: `{spelling}` is a domain and not an address",
              "." in spelling and "@" not in spelling and " " not in spelling)

    print()
    print("the vendored copy is the half above the sentinel, and it parses")
    hook = render()
    head_only = hook.split(RENDER_TAIL)[0]
    check("it parses as python", _parses(hook))
    check("it carries the rule", "def strip(" in hook and "def attribution(" in hook)
    check("it carries no renderer and no suite",
          "def render(" not in head_only and "def self_test(" not in head_only)
    # ⛔ Derived from the fixtures rather than written out as literals. ⚠️ Three
    # hand-written spellings was the first form of this arm, and it is the shape
    # that goes quietly wrong: a fixture renamed leaves the arm green while the
    # spelling it was guarding against is still free to reach an adopting
    # repository. ⚠️ **The addresses and the display names, and not the marker
    # line** -- that one carries a product name the list legitimately states, so
    # including it would make the arm refuse the hook for carrying its own rule.
    # ⚠️ **Case-sensitively**, which is a property of the field and not a
    # loosening: a display name is a proper noun and its capitals are part of
    # it. ⚠️ Measured case-insensitively, where the generic fixture names matched
    # the rule's own English above the sentinel -- *a tool in the contributor
    # graph*, *a person who actually worked on the change* -- and the arm refused
    # the hook for carrying its own documentation.
    planted = _planted_spellings((tool, bot, human, namesake))
    reached = sorted(spelling for spelling in planted if spelling in hook)
    check("it carries none of the suite's planted spellings", not reached, str(reached))
    check("it keeps the shebang on the first line", hook.startswith("#!"))
    check("it ends by running the hook", hook.endswith(RENDER_TAIL))
    check("it imports nothing of this toolkit's",
          _imports(hook) <= {"__future__", "argparse", "os", "re", "sys"},
          str(_imports(hook)))
    # ⛔ The arm that makes the sentinel load-bearing. ⚠️ Measured with the split
    # taken out: the whole file was vendored, carrying a planted person's address
    # into every adopting repository, and every other arm above stayed green.
    check("and a render of a file with no sentinel is refused",
          _refuses_without_sentinel(), "a file with no sentinel rendered anyway")

    # ⛔ Run as itself and not merely parsed: the vendored copy is what git calls,
    # so a strip that works here and not there is the one failure this split can
    # produce.
    with tempfile.TemporaryDirectory() as tmp:
        where = os.path.join(tmp, "commit-msg")
        with open(where, "w", encoding="utf-8") as handle:
            handle.write(hook)
        message = os.path.join(tmp, "COMMIT_EDITMSG")
        with open(message, "w", encoding="utf-8") as handle:
            handle.write(f"Subject\n\nBody.\n\n{human}\n{tool}\n")
        import subprocess
        done = subprocess.run([sys.executable, where, message],
                              capture_output=True, text=True, check=False)
        with open(message, encoding="utf-8") as handle:
            left = handle.read()
        check("the vendored copy runs and strips", done.returncode == 0,
              done.stderr.strip())
        check("  to the same bytes this module produces",
              left == f"Subject\n\nBody.\n\n{human}\n", repr(left))

    print()
    print(f"{ran} arm(s) ran.")
    # ⛔ A run that executed nothing is a failure and not a pass, which is the
    # floor every other arm rests on.
    if ran == 0:
        print("no arm ran, so this run asserts nothing.", file=sys.stderr)
        return 1
    if failures:
        print(f"{len(failures)} arm(s) failed: {', '.join(failures)}", file=sys.stderr)
        return 1
    print("every arm held.")
    return 0


def _parses(text: str) -> bool:
    import ast
    try:
        ast.parse(text)
    except SyntaxError:
        return False
    return True


def _imports(text: str) -> set[str]:
    """Every top-level module name this text imports."""
    import ast
    found: set[str] = set()
    for node in ast.walk(ast.parse(text)):
        if isinstance(node, ast.Import):
            found.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            found.add(node.module.split(".")[0])
    return found


def _planted_spellings(lines) -> set[str]:
    """Every address and display name these planted trailers carry.

    ⛔ The whole field and never a fragment of it. The vendor domain the list
    legitimately states is a fragment of one of these addresses, so an arm
    testing fragments would refuse the hook for carrying the rule it ships.
    """
    found: set[str] = set()
    for line in lines:
        trailer = CO_AUTHOR.match(line)
        if trailer is None:
            continue
        value = trailer.group("value")
        address = _address_of(value)
        if address:
            found.add(address)
        name = ADDRESS.sub("", value).strip()
        if name:
            found.add(name)
    return found


def _refuses_without_sentinel() -> bool:
    """Whether `render` refuses a copy of this file carrying no sentinel.

    ⚠️ Asserted by pointing the renderer at a planted file rather than by
    reading its source: what the arm is about is the refusal happening, and a
    grep for the `raise` would pass against a branch nothing reaches.
    """
    import tempfile
    global __file__  # noqa: PLW0603 -- restored in the `finally` below
    original = __file__
    try:
        with tempfile.TemporaryDirectory() as tmp:
            planted = os.path.join(tmp, "no-sentinel.py")
            with open(planted, "w", encoding="utf-8") as handle:
                handle.write("#!/usr/bin/env python3\nx = 1\n")
            __file__ = planted
            try:
                render()
            except ValueError:
                return True
            return False
    finally:
        __file__ = original


if __name__ == "__main__":
    if "--self-test" in sys.argv[1:]:
        sys.exit(self_test())
    # ⛔ Dispatched here and not inside `main`, which is the half the install step
    # vendors: a flag for the render in that parser would ship an adopting
    # repository a hook that can be asked to print itself, and the one thing the
    # hook is given is a message file.
    if "--render" in sys.argv[1:]:
        print(render(), end="")
        sys.exit(0)
    sys.exit(main())
