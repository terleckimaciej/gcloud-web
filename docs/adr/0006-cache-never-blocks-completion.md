# 0006. Cache: completion never waits for the network

- Status: Accepted
- Date: 2026-10-11

## Context

gcloud keeps its completion cache for 1 h and, once it expires, synchronously runs the list command on TAB, which means seconds of waiting. Resource names rarely change, and a stale entry results at worst in a 404 page in the console. The same cache is later meant to feed the wizard (stage 2).

## Decision

- Cache in `~/.cache/gcw/<account>/<project>/<type>.json` (respecting `XDG_CACHE_HOME`): a flat list of `{name, location, extra}` plus a timestamp. Atomic writes (temporary file + `rename`).
- `__complete` reads the cache only. It does no network access and spawns no subprocesses.
- No hard expiry. After 24 h an entry is "soft stale": using it starts a detached process that refreshes it in the background.
- `gcw refresh [type]` forces a refresh. A name missing from the cache when opening (not on TAB) triggers one live request and adds the result.
- The resource location from the cache replaces the `--region` and `--zone` flags.

## Consequences

TAB and the wizard are instant. Right after a new resource is created, the first TAB may not know it: background refresh or `gcw refresh`. The first run in a project has an empty cache, so it is filled in the background on first use.
