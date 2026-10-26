# 0020. gcloud command syntax as gcw input

- Status: Proposed
- Date: 2026-10-24

## Context

Most users reach a resource through gcloud first: a `describe`, a `list`, a `deploy`. Turning that command into the matching console page currently means rewriting it by hand in gcw syntax ([ADR-0012](0012-cli-syntax-and-routes.md)).

[ADR-0019](0019-service-names-follow-gcloud.md) made service names equal to gcloud's command groups, and kind names already are gcloud's collections, so the two syntaxes now share every noun. They still differ in three ways:

- gcloud has verbs (`describe`, `list`, `update`, `deploy`…); gcw has none, because its only action is "open".
- gcloud flags carry the context (`--region`, `--zone`, `--location`, `--project`, `--configuration`), and gcloud accepts many flags gcw has no use for (`--format`, `--quiet`…).
- gcloud has sub-groups gcw does not model (`gcloud run jobs executions …`, `gcloud secrets versions …`).

A plain shell alias that forwards the words to gcw therefore fails on most real commands. [ADR-0015](0015-no-gcloud-shell-wrapper.md) also rules out the obvious packaging: gcw must not wrap or shadow `gcloud`.

The translation itself, "gcloud command path → console page", is the part of gcw that would matter to anyone building a native `--web` flag into gcloud.

## Decision

### `gcw gcloud ARGS…`

gcw gets a subcommand that takes a gcloud command line and opens the page it refers to. The leading word is literally `gcloud`, so a command from shell history becomes a gcw command by prefixing it with `gcw `:

```
gcw gcloud run jobs describe nightly --region europe-west1
  → same as: gcw run jobs nightly -l europe-west1
gcw gcloud container clusters list
  → same as: gcw container clusters
```

The subcommand translates the arguments into gcw arguments and runs them through the normal command path, so context resolution, the cache, `authuser` and `-n` behave exactly as in ADR-0012. gcw global flags go before `gcloud` (`gcw -n gcloud …`). The translated gcw command is printed to stderr, so the user learns the shorter spelling.

### Translation rules

1. **Service.** The first word is matched against the service names, which are gcloud's command groups (ADR-0019). A word matching only a start page opens that page.
2. **Kind.** The next word is the kind, as in ADR-0012. Single-kind services (`functions`, `secrets`) skip it.
3. **Verb.** The next word must be a known gcloud verb, from one data table. `list` opens the list page; any other verb followed by a name opens that resource; a verb without a name opens the list.
4. **Name.** The first positional after the verb. Known prefixes are stripped where gcloud accepts a URI (`gs://bucket` → `bucket`).
5. **Flags.** `--region`, `--zone`, `--location` → `-l`; `--project` → `-p`; `--configuration` → `-c`. `--web` is accepted and ignored. Every other flag is ignored; an unknown `--flag value` (without `=`) swallows the following word as its value, so positionals are read only before the first flag.
6. **Anything else**, such as an unknown group, kind, or a sub-group in place of a verb, is an error naming the deepest page gcw does know ("gcw does not know `gcloud run jobs executions`; nearest: `gcw run jobs`"), with exit code 2. gcw never guesses beyond the registry.

All of this is data: the verb table and flag map live in one module, and services need no new attribute, because their names already are gcloud's. Adding a service adds no translation code.

### Shell integration stays the user's

gcw ships no `gcloud` function; ADR-0015 stands. The README documents, as a recipe for the user's own shell configuration, a function that forwards `gcloud … --web` to `gcw gcloud …`. Nothing installs it.

### Completion

`gcw gcloud` has no TAB completion, by design. The intended way in is the user's `gcloud … --web` function: a command from history gets ` --web` appended. On that line TAB belongs to gcloud's own completion, which shells bind to the `gcloud` command name, and hooking gcw's suggestions into it would mean wrapping gcloud's completion, the wrapper ADR-0015 rejected. Completing `gcw gcloud …` itself would only help someone typing a gcloud command from scratch, and for that the plain gcw syntax already completes resource names from the cache.

So the roles are: `gcw <service> <kind> <TAB>` to explore and type from scratch, `gcloud … --web` to turn a command from history into a page, and `gcw gcloud …` as the stable entry point underneath, which also works without the shell function (in scripts, PowerShell, or for users who have not added the recipe).

## Consequences

- Any supported gcloud command from history opens its console page by adding `gcw ` in front, in every shell and in scripts, with no wrapper (ADR-0015 holds).
- The registry doubles as a "gcloud command → console URL" mapping, which is the dataset a native `gcloud … --web` would need.
- Coverage is limited to the registry. Unknown commands fail with a pointer, never with a wrong page.
- Positional detection after unknown flags is a heuristic: a bare word after an unknown boolean flag is misread as its value. This is acceptable, because gcloud commands put positionals before flags in practice.
- ADR-0019 keeps the translation down to dropping verbs and mapping flags; a future service named differently from its gcloud group would break it, which is one more reason ADR-0019 has no exceptions.
- One new CLI module; the completion path is untouched.
