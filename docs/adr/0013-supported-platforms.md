# 0013. Supported platforms and CI

- Status: Accepted
- Date: 2026-10-13

## Context

The user works on Linux, and on Windows in Git Bash. gcw is pure Python with no shell dependencies, so it runs wherever Python runs. A few places do behave differently per system:
- the gcloud configuration directory (`%APPDATA%\gcloud` on Windows);
- running gcloud (`gcloud.cmd` on Windows);
- detaching the cache refresh process;
- the cache directory;
- shell-dependent TAB completion.

gcloud's completion usually does not work in Git Bash on Windows, probably because its mechanism (modelled on argcomplete) passes results through file descriptors and environment variables that do not make it through `gcloud.cmd`.

## Decision

- **Supported systems:** Linux, macOS and Windows.
- **Shells:**
  - bash, zsh and fish (including **Git Bash** on Windows): full support, including TAB completion and `gcloud web`. Our completion script calls `gcw __complete`, an ordinary executable (`gcw.exe` on Windows), so gcloud's problem does not affect us;
  - cmd and PowerShell: all commands work, without TAB completion and without `gcloud web`. PowerShell completion (`Register-ArgumentCompleter` calling `gcw __complete`) is in the backlog;
  - WSL: works, except that the browser is on the Windows side, so `BROWSER=wslview` may be needed (described in the README).
- **Python:** >= 3.11.
- **CI (GitHub Actions, `.github/workflows/ci.yml`):** Python 3.11 on Ubuntu, macOS and Windows, plus Python 3.13 on Ubuntu. Platform differences and Python version differences are independent, so each dimension is covered without the full product. The aggregate `ci` job is the only required check in the `master` protection (together with requiring a PR, administrators included).

## Consequences

- System-dependent code needs a Windows variant. To remember in M3: `shutil.which("gcloud")` (finds `gcloud.cmd`), separate process-detaching flags, `%LOCALAPPDATA%\gcw` as the cache directory.
- Tests have to pass on all three systems. CI enforces this on every PR.
- The `master` protection blocks direct pushes, so every change, urgent ones included, goes through a PR.
