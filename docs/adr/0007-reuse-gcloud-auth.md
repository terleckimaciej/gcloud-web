# 0007. Authentication shared with gcloud

- Status: Superseded by [0016](0016-official-token-command-by-default.md) (the ordering is reversed: the official command is the default, the database read is opt-in)
- Date: 2026-10-11

## Context

Refreshing the cache requires an access token. A separate login (ADC) is an extra step that expires with the corporate session policy anyway. gcloud keeps a valid token in `access_tokens.db` (sqlite) and refreshes it itself with the refresh token. `gcloud auth print-access-token` costs ~1 s, but the token is only needed on the background refresh path.

## Decision

1. Read `access_tokens.db` (table `access_tokens`: `account_id`, `access_token`, `token_expiry`) for the active account. The token is used if at least 5 minutes of validity remain.
2. Otherwise, or on any error: `gcloud auth print-access-token [--account]`.
3. No gcloud or an expired session: a readable message saying to run `gcloud auth login`. URLs that need no cache (L0, `open`) keep working.

## Consequences

No extra login, the same permissions as in gcloud. The database format is internal, which is why step 2 always remains the fallback. Nothing is ever written to the database.
