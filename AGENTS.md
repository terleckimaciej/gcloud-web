# AGENTS.md

Instructions for AI agents (Claude Code, Codex, etc.) working in this repository.

## Project

`gcw` ("gcloud web"): a `gh browse`-style CLI that opens Google Cloud services and resources in the browser, taking context from the gcloud configuration and offering instant TAB completion of resource names.

- Plan and progress: [docs/plan.md](docs/plan.md). Tick checkboxes and the Status column once something is done and verified.
- Decisions: [docs/adr/](docs/adr/). Research: [docs/research.md](docs/research.md).
- `docs/` is local-only for now (see "Workflow") and is written in Polish.

## Rules that require a new ADR to break

- **Runtime uses the standard library only.** Third-party packages are allowed in the dev group only (pytest, etc.).
- **gcw navigates, gcloud operates.** No commands that change the state of cloud resources.
- **The completion path (`gcw __complete`) never touches the network or spawns subprocesses**; it reads the cache only. Budget: < 50 ms. Do not add slow top-level imports; import lazily inside functions that are not on the completion path.
- **URL routes are data, not logic.** Adding a service is primarily a registry entry, and every URL template must be verified against the real console.
- **Do not import gcloud's code.** Read gcloud's files only where an ADR allows it (INI config, `access_tokens.db`), always with a fallback to the `gcloud` command.

## Stack and commands

- Python >= 3.11 (`tomllib`), uv, `src/` layout.
- `uv sync` to set up the environment, `uv run pytest` to run tests, `uv run gcw …` to run the CLI.
- Tests must not use the network or the real `~/.config/gcloud`. Use a fake `CLOUDSDK_CONFIG` under `tmp_path`.

## Workflow

- **The user reviews every edit and wants to understand it.** For every file change, briefly explain (in Polish, in the chat) what you are changing, why, and how it connects to the rest of the code. Avoid large unexplained changes; split work into steps that can be read and understood one at a time.
- **Only code and agent configuration are committed.** `docs/` (plan, research, ADRs) is excluded locally via `.git/info/exclude`. Never add it to commits.
- **Everything committed is in English**: code, identifiers, docstrings, comments, CLI messages, commit messages, this file. Local `docs/` stays in Polish.

## Commits and pull requests

- **Every change goes through a pull request into `master`**; never commit directly to `master`. Work on a branch named `<type>/<short-description>` (e.g. `feat/gcloud-config`).
- **The user runs git and gh, not the agent.** Never run `git add`, `git commit`, `git push`, branch-switching commands or `gh pr create` yourself. Instead, propose in the chat the ready-to-paste commands together with the commit message and the PR title/description, so the user can adjust them before running.
- Format: [Conventional Commits](https://www.conventionalcommits.org/), `type: description` or `type(scope): description`.
  - Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build` (packaging, dependencies, uv), `ci`, `chore`.
  - Scope is optional. Use it only when it adds information: a layer (`cli`, `context`, `cache`, `api`, `web`, `services`) or a GCP service (`run`, `sql`, …). Omit it for cross-cutting changes; never force one.
  - Description: imperative mood, lowercase, no trailing period, about 72 characters max. Mark breaking changes with `!` (e.g. `feat(cli)!: …`).
- The PR title uses the same format, because it becomes the commit message on squash merge. The PR description explains what changed and why, and how it was verified.

## ADRs

- A significant decision (a dependency, a data format, user-visible behavior, an exception to the rules above) requires a new `docs/adr/NNNN-short-title.md` based on the [template](docs/adr/template.md).
- Do not rewrite accepted ADRs. Record a new decision as a new ADR with `Status: Accepted, supersedes NNNN`, and set `Superseded by NNNN` in the old one.

## Conventions

- **English docstrings are mandatory** for every module (what it does and what it is responsible for), class, function and method, including service modules (which GCP service it covers: routes, tabs, where the resource list comes from). Style: a one-line summary; for non-trivial logic, add a description, arguments and the return value.
- Inline comments only where the code does not speak for itself.
