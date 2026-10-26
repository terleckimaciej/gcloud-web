# 0023. No opt-in for reading access_tokens.db

- Status: Accepted, partially supersedes [0016](0016-official-token-command-by-default.md) (the `GCW_FAST_TOKEN` opt-in)
- Date: 2026-10-26

## Context

[ADR-0016](0016-official-token-command-by-default.md) gets access tokens from `gcloud auth print-access-token` and allowed an opt-in, `GCW_FAST_TOKEN=1`, to read them from `access_tokens.db`, gcloud's internal sqlite store. The command costs about a second; the file read about a millisecond.

With the cache in place, a token is needed only when gcw calls an API:

- a background refresh of a stale or empty cache, which nobody waits for;
- `gcw cache refresh`, which takes several seconds anyway;
- a live lookup of a name missing from the cache, which is rare (e.g. right after creating a resource).

TAB completion and opening a cached resource need no token at all. The opt-in would save about a second, rarely.

Against that: the file's format is undocumented and may change in any gcloud release, and reading a credential store is the first thing a security review looks at. The README promises that gcw does not read gcloud's credential store.

## Decision

- gcw gets tokens only from `gcloud auth print-access-token`. There is no `GCW_FAST_TOKEN` and no code that reads `access_tokens.db`.
- The only gcloud files gcw reads are its configuration files ([ADR-0005](0005-context-from-gcloud-config.md)).
- The rest of ADR-0016 stands.

## Consequences

- One code path for tokens, nothing internal to gcloud to track, and the README's security statement holds without exceptions.
- A live lookup or manual refresh takes about a second longer than it could.
- Revisiting this needs a new ADR and a case where the second matters.
