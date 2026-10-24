# 0016. Access tokens come from the official gcloud command by default

- Status: Accepted, supersedes [0007](0007-reuse-gcloud-auth.md)
- Date: 2026-10-19

## Context

[ADR-0007](0007-reuse-gcloud-auth.md) reads the active account's token from `access_tokens.db`, gcloud's internal sqlite store, and falls back to `gcloud auth print-access-token`. The ordering was chosen for speed: the command costs ~1 s, the file read ~1 ms.

Two things argue against that default now:

- `access_tokens.db` is a private credential store. Reading it by default is the first item a corporate security review has to analyse, and the hardest to justify for a navigation tool.
- The token is needed only on the background cache-refresh path. That path is already detached and asynchronous, so ~1 s there is invisible to the user. The optimisation buys nothing the user can feel.

## Decision

- The default source of an access token is `gcloud auth print-access-token [--account]`.
- Reading `access_tokens.db` is an explicit opt-in (`GCW_FAST_TOKEN=1`) for users who want the faster path and accept that the format is internal. It is read-only; gcw never writes to it.
- gcw does not read any other internal gcloud state. In particular it does not read gcloud's completion cache (`<config>/cache/<account>/resource.cache`), even though it holds resource names: gcw maintains its own cache ([ADR-0006](0006-cache-never-blocks-completion.md)).
- Reading gcloud's INI configuration files stays as decided in [ADR-0005](0005-context-from-gcloud-config.md): a documented-in-practice, stable format, with `gcloud config list --format=json` as the fallback.
- No gcloud session, or no gcloud at all: a readable message pointing at `gcloud auth login`. URLs that need no cache keep working.

## Consequences

- The default path uses a supported, public interface, so the security posture is one sentence: gcw runs `gcloud` and reads configuration files.
- Background refresh takes about a second longer unless the opt-in is set.
- Two code paths instead of one, behind one function. The opt-in has to be covered by tests and documented in the README.
