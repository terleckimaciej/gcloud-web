# 0024. gcw prints an opt-in `gcloud … --web` shell function

- Status: Accepted, partially supersedes [0015](0015-no-gcloud-shell-wrapper.md) (gcw ships no `gcloud` function)
- Date: 2026-10-26

## Context

[ADR-0020](0020-gcloud-syntax-input.md) adds `gcw gcloud ARGS…`, which opens the console page of a gcloud command line. The most natural way to use it is to append `--web` to a gcloud command from shell history. That needs a shell function named `gcloud`, and [ADR-0015](0015-no-gcloud-shell-wrapper.md) decided that gcw ships none; ADR-0020 therefore left the function to a README recipe.

ADR-0015 rejected `gcloud web …`, a function that took over a whole subcommand. Its reasons apply differently to a function that only reacts to `--web`:

- **Shadowing a command someone else maintains.** The function changes nothing for gcloud's own commands: every command line without `--web` runs `command gcloud "$@"` unchanged. gcloud has no `--web` flag, so the lines it takes over are ones gcloud would reject.
- **gcloud's completion.** Shells bind completion to the command name, so the function keeps gcloud's TAB completion without wrapping it.
- **Working only in some shells.** True, and acceptable for a convenience: `gcw gcloud …` is the entry point that works everywhere (scripts, PowerShell, cmd), and the function is only a shorter way to reach it.
- **Reading gcw as part of gcloud.** The function is printed by gcw and enabled by the user by name (`gcw web-flag`), so where `--web` comes from stays visible.

A README recipe would leave every user to copy, adapt per shell and maintain the same function by hand, which is what `gcw completion` already avoids for TAB.

## Decision

- `gcw web-flag bash|zsh|fish` prints a shell function named `gcloud`. A command line containing `--web` goes to `gcw gcloud …` with the same arguments; every other one runs `command gcloud "$@"`.
- Nothing installs it. The user enables it by adding one line to the shell's startup file, as for completion: `eval "$(gcw web-flag bash)"` in `~/.bashrc` (zsh: `~/.zshrc`), `gcw web-flag fish | source` in `~/.config/fish/config.fish`. README and `gcw web-flag --help` give these lines.
- The rest of ADR-0015 stands: gcw writes nothing into gcloud's configuration directory and does not change what gcloud does with any command line it accepts.

## Consequences

- `gcloud run jobs describe nightly --web` opens the job's page for users who enable the function; others use `gcw gcloud …` or plain gcw syntax.
- If gcloud ever gains its own `--web` flag, the function would hide it. The function is opt-in and named after the flag, so the user can drop the line; gcw would then reconsider this ADR.
- Three more shell scripts to maintain and test, next to the completion scripts.
