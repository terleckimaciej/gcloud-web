# 0015. No shell wrapper around gcloud

- Status: Accepted, supersedes [0009](0009-gcloud-web-shell-wrapper.md); partially superseded by [0024](0024-opt-in-gcloud-web-function.md) (an opt-in `gcloud … --web` function)
- Date: 2026-10-19

## Context

[ADR-0009](0009-gcloud-web-shell-wrapper.md) added `gcw shell-init`, which prints a shell function named `gcloud`. The function intercepts `gcloud web …` and delegates everything else to `command gcloud "$@"`.

The project's target changed: gcw should be presentable to Google engineers and adoptable inside a company as an internal open-source tool. Under that goal the wrapper is the weakest part of the design:

- It shadows a command maintained by someone else. Opt-in or not, it changes the behaviour of `gcloud` in that shell.
- It interacts with gcloud's own completion, which has to be wrapped as well.
- It works only in shells that sourced it: not in scripts, not under `xargs`, not in `cmd` or PowerShell. So `gcloud web` is a command that works for some invocations and not others — the worst property a command can have.
- It invites the reading that gcw is an extension of gcloud, which it is not.

## Decision

gcw does not wrap, shadow or extend the `gcloud` command. The only entry point is the `gcw` executable. `gcw shell-init` is dropped from the scope.

Anyone who wants the shorter spelling can add their own shell alias; that is their shell configuration, not something gcw installs.

This generalises to a project rule: gcw does not change the behaviour of gcloud and writes nothing into gcloud's configuration directory.

## Consequences

- One command, one behaviour, in every shell and in scripts. Nothing to document about shells that lack support.
- The `gcloud web` spelling is gone, including its completion wrapper.
- Security and platform review has nothing to analyse here: gcw is an ordinary executable that reads configuration files.
- Shell integration is reduced to what gcw owns: completion scripts for `gcw` itself.
