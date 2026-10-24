# 0004. gcw navigates, gcloud operates

- Status: Accepted
- Date: 2026-10-11

## Context

With a resource cache and a token in hand, it is easy to keep adding `describe`, `deploy`, VM actions and so on. The tool would then start duplicating gcloud and bloat.

## Decision

gcw only builds and opens console URLs. The only exceptions are views of what we navigate: `gcw ls` (a table from the cache) and `gcw services`. No operations that change the state of resources.

## Consequences

A small scope and a clear boundary. Read-only permissions (`list`) are enough. Requests for "actions" are referred to gcloud.
