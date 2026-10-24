# 0009. `gcloud web` through an optional shell wrapper

- Status: Superseded by [0015](0015-no-gcloud-shell-wrapper.md)
- Date: 2026-10-11

## Context

Calling `gcloud web …` would look like an official extension. As far as we know, gcloud has no mechanism for external plugins like `gh-<name>` (only Google distributes components).

## Decision

The `gcw` executable is the foundation. `gcw shell-init bash|zsh|fish` prints a `gcloud` function that intercepts a first argument of `web` and delegates to `gcw`, and in every other case calls `command gcloud "$@"`. Completion for `gcloud web` is a wrapper around gcloud's existing completion function. Enabled with `eval "$(gcw shell-init bash)"`.

## Consequences

Optional and harmless to gcloud, because it only works in shells that enabled it. It does not work in scripts without `eval` or outside a shell (e.g. under `xargs`); `gcw` has to be used there.
