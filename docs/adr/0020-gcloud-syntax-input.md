# 0020. gcloud command syntax as gcw input

- Status: Accepted
- Date: 2026-10-24 (proposed), 2026-10-26 (accepted with the rules below)

## Context

Most users reach a resource through gcloud first: a `describe`, a `list`. Turning that command into the matching console page currently means rewriting it by hand in gcw syntax ([ADR-0012](0012-cli-syntax-and-routes.md)).

[ADR-0019](0019-service-names-follow-gcloud.md) made service names equal to gcloud's command groups, and kind names already are gcloud's collections, so the two syntaxes share every noun. They still differ in three ways:

- gcloud has verbs (`describe`, `list`, `update`, `deploy`…); gcw has none, because its only action is "open".
- gcloud flags carry the context (`--region`, `--zone`, `--location`, `--project`, `--configuration`), and gcloud accepts many flags gcw has no use for (`--format`, `--quiet`…).
- gcloud has sub-groups gcw does not model (`gcloud run jobs executions …`, `gcloud secrets versions …`).

A plain shell alias that forwards the words to gcw therefore fails on most real commands.

The translation itself, "gcloud command path → console page", is the part of gcw that would matter to anyone building a native `--web` flag into gcloud.

## Decision

### `gcw gcloud ARGS…`

gcw gets a subcommand that takes a gcloud command line and opens the page it refers to. The leading word is literally `gcloud`, so a command from shell history becomes a gcw command by prefixing it with `gcw `. The usual way in is `gcloud … --web` through the opt-in shell function of [ADR-0024](0024-opt-in-gcloud-web-function.md), which calls `gcw gcloud …`.

```
gcloud run jobs describe nightly --region europe-west1 --web
  → gcw run jobs nightly --region europe-west1
gcloud run jobs describe nightly --web
  → gcw run jobs nightly            (location from the cache or the configuration)
gcloud container clusters list --web
  → gcw container clusters
```

The subcommand translates the words into gcw arguments and runs them through the normal command path, so context resolution, the cache, `authuser` and `-n` behave exactly as in ADR-0012. Before opening, it prints the translated gcw command to stderr, keeping the flag spelling the user typed (gcw accepts `--region`, `--zone` and `--location` as aliases of `-l`), so the user sees that the plain gcw command takes the same words.

### Translation rules

1. **Service.** The first word is matched against the service names, which are gcloud's command groups (ADR-0019). A word matching only a start page opens that page, whatever follows.
2. **Kind.** The next word is the kind, as in ADR-0012. Single-kind services (`functions`, `secrets`) skip it. One group-level read command maps to a kind: `gcloud storage ls gs://BUCKET[/PATH]` → `gcw storage buckets BUCKET[/PATH]`.
3. **Verb.** Only commands that read are translated: `describe`, `get-iam-policy` and `list`, from one data table. `list` opens the list page; a read verb followed by a name opens that resource; a read verb without a name opens the list.
4. **Early end.** A command that ends before its verb opens the page for the words given, as gcw does: `gcloud run jobs` → `gcw run jobs` (the list), `gcloud run` → `gcw run`, `gcloud` → `gcw` (the project dashboard).
5. **Name.** The first positional after the verb, passed on as typed. gcw itself accepts a bucket as gcloud prints it, so `gs://bucket/path` works both here and in `gcw storage buckets gs://bucket/path` (the route's `name_prefix`).
6. **Flags.** `--region`, `--zone`, `--location`, `--project` and `--configuration` pass to gcw unchanged, because gcw accepts the same names. gcw's own `-n`/`--no-browser` and `--no-authuser`, which gcloud does not have, pass too, so `gcloud … --web -n` prints the URL. `--web` is dropped. Every other flag is ignored; an unknown `--flag value` (without `=`) swallows the following word as its value, so positionals are read only before the first flag.
7. **Anything else** is an error with exit code 2 that names the nearest page gcw knows: a word in the verb position that is not a read verb (a command that changes resources, such as `update` or `deploy`, or a sub-group such as `executions`), an unknown group or an unknown kind. The message says that gcw only opens pages and that the command runs in gcloud without `--web`:

   ```
   gcw: `gcloud run jobs update` is not a command gcw can open; gcw only opens pages.
        Run it without --web. Nearest page: gcw run jobs
   ```

   gcw never guesses beyond the registry, and never opens a page for a command that was meant to change something.

All of this is data: the verb table, the group-level commands and the flag map live in one module, and services need no new attribute, because their names already are gcloud's. Adding a service adds no translation code.

### Completion

`gcw gcloud` has no TAB completion of the gcloud words, by design. On a `gcloud … --web` line TAB belongs to gcloud's own completion, which shells bind to the `gcloud` command name; hooking gcw's suggestions into it would mean wrapping gcloud's completion. Completing `gcw gcloud …` itself would only help someone typing a gcloud command from scratch, and for that the plain gcw syntax already completes resource names from the cache.

So the roles are: `gcw <service> <kind> <TAB>` to explore and type from scratch, `gcloud … --web` to turn a command from history into a page, and `gcw gcloud …` as the stable entry point underneath, which also works without the shell function (in scripts, PowerShell, cmd).

## Consequences

- Any supported read command from gcloud's history opens its console page, through `gcloud … --web` or by prefixing it with `gcw `.
- A command that changes resources never opens a page in its place, so `--web` cannot be mistaken for "do it and show me".
- The registry doubles as a "gcloud command → console URL" mapping, which is the dataset a native `gcloud … --web` would need.
- Coverage is limited to the registry and the read verbs. Other commands fail with a pointer, never with a wrong page.
- Positional detection after unknown flags is a heuristic: a bare word after an unknown boolean flag is misread as its value. This is acceptable, because gcloud commands put positionals before flags in practice.
- ADR-0019 keeps the translation down to dropping verbs and mapping flags; a future service named differently from its gcloud group would break it, which is one more reason ADR-0019 has no exceptions.
- One new CLI module; the completion path is untouched.
