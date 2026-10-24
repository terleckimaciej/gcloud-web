# 0018. Cache commands live under `gcw cache`

- Status: Accepted
- Date: 2026-10-24

## Context

The MVP plan named the cache commands `gcw ls [type]` and `gcw refresh [type]`, and they shipped that way. Using them raised three problems:

- The top level of gcw is nouns: GCP services (`gcw run`, `gcw sql`, dozens of start pages), `gcw services` and `gcw open`. `ls` and `refresh` were the only verbs, and `gcw ls` reads like it could be one more service.
- `gcw ls` suggests "list the resources of the project", like `gcloud … list`. It actually prints a snapshot of the local cache, which may be up to a day old and is incomplete by design (APIs disabled in the project, Dataproc and Composer listed in one region).
- `gcw refresh` does not say what it refreshes.

Other tools treat a cache as a noun with actions: `pip cache list|purge|dir`, `uv cache clean|dir|prune`, `npm cache clean|verify`, `gh cache list|delete`. Top-level verbs such as `apt update` or `brew update` exist where refreshing is the everyday, primary action. In gcw it is not: stale entries refresh themselves in the background ([ADR-0006](0006-cache-never-blocks-completion.md)), and a manual refresh is needed only right after creating a resource.

## Decision

```
gcw cache list [SERVICE [KIND]]       show the cached resources (alias: gcw cache ls)
gcw cache refresh [SERVICE [KIND]]    fetch resource names into the cache
```

- `cache` is a top-level noun; `list` and `refresh` are its required actions. `ls` is an alias of `list`, as in docker and gh.
- `gcw ls` and `gcw refresh` are removed, without aliases, since gcw has not been released.
- Further maintenance actions, when needed, become subcommands of the same noun (e.g. `gcw cache clear`, `gcw cache path`).

## Consequences

- The command names say where the data comes from and that it can be stale.
- The top level stays a namespace of nouns, so a future service named like a verb cannot collide with a cache action.
- Typing is longer, which is acceptable for commands needed rarely; TAB completion offers them.
- Breaking change for anyone who tried the earlier names; messages, the background refresh process and the plan use the new ones.
