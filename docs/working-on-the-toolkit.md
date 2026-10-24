# Working on the toolkit: what registering it writes, and what a session serves

The two commands that register this tree as its own marketplace are on the front page, under
[*Working on the toolkit itself*](../README.md#working-on-the-toolkit-itself). ⚠️ **Register, not
install into a project**: the second sense is the artifacts the toolkit writes into an adopting
repository, which is
[`schema.md`'s own section](../plugins/mjolnir/config/schema.md#what-the-toolkit-installs-into-a-project-and-what-takes-it-out)
and not this document. What these two commands write,
which copy of the plugin a session resolves, and the two consequences of that worth knowing before
editing are here — one hop off the front page, because the reader of this document is whoever is
editing this tree rather than whoever is deciding whether to adopt it. The single statement of
every rule and flow is
[`../plugins/mjolnir/config/schema.md`](../plugins/mjolnir/config/schema.md); this document states
none of them.

## The scope is `user`, and `local` is not a narrower one

`user` rather than `local`, because whoever works on the toolkit is also the person adopting it in
every other project on the same machine, and one registration serves both: self-hosting here, and
every other project — whose adoption then costs one file to write, `.claude/mjolnir.yaml`, and no
second registration of its own. ⚠️ **What the toolkit writes back into such a project** — the
artifacts only its host and its git can read — is a different act from the registration this
document is about, and is
[`schema.md`'s own section on it](../plugins/mjolnir/config/schema.md#what-the-toolkit-installs-into-a-project-and-what-takes-it-out).

`local` does not confine a registration the way its name suggests, which is the sharper reason to
pass `user` explicitly rather than a matter of reach. Only the *declaration* lands in one project's
`.claude/settings.local.json`; the registry entry that resolution actually reads is machine-wide and
keyed by marketplace name. Measured: a project declaring nothing of its own resolved the plugin
from an entry a different project's `local` add had written, a second `local` add of the same name
re-pointed that entry for every project instead of coexisting with the first, and a `remove` from
one project emptied it for all of them — leaving the first project's own declaration pointing at
nothing. So `local` is not a narrower `user`; it is the same machine-wide entry with its declaration
filed somewhere that does not govern it.

## What those two commands write

So the choice is checkable rather than asserted. Paths are inside the harness's own user
configuration directory, wherever `CLAUDE_CONFIG_DIR` puts it:

| | |
|---|---|
| `settings.json` | `extraKnownMarketplaces.mjolnir` — `source: directory` with the path — and `enabledPlugins["mjolnir@mjolnir"]` |
| `plugins/known_marketplaces.json` | `installLocation`, which for a directory source **is the working tree** |
| `plugins/installed_plugins.json` | `scope`, a `version`, a `gitCommitSha`, and an `installPath` under `plugins/cache/` |

**That `installPath` is a snapshot copy, and it is vestigial.** It is written once, at install, and
pinned to the recorded `gitCommitSha`. Nothing refreshes it: `plugin marketplace update` leaves it
alone, and `plugin update` is version-gated, so it reports the plugin already at its latest version
while the snapshot stays where it was. Measured in this repository: the snapshot was byte-identical
to its pinned commit, three commits behind the branch tip, and differed from the tree in six of its
seven files.

## What a session actually serves

Edits are live anyway, because a session resolves a directory-source plugin through the
marketplace's `installLocation` — the working tree — and never through `installPath`.
`$CLAUDE_PLUGIN_ROOT` resolves there too, so plugin-provided scripts and hooks also run from the
tree. Reading `installPath` and concluding the install is frozen is reading the copy nothing serves.

Two consequences of that, worth knowing before editing:

- A session started **afterwards** serves an edited skill or `hooks/hooks.json` with no reinstall,
  no `plugin update` and no version bump. A session already running keeps the configuration it
  started with.
- Only the registered tree is served, so a branch in a git worktree is served **nowhere** until it
  reaches that tree. A change to the procedure cannot be dogfooded from the worktree it was written
  in.
