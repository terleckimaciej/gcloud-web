# AGENTS.md

Instructions for AI agents (Claude Code, Codex, etc.) working in this repository.

## Project

`gcw` ("gcloud web"): a `gh browse`-style CLI that opens Google Cloud services and resources in the browser, taking context from the gcloud configuration and offering instant TAB completion of resource names.

- Open work: GitHub issues (`gh issue list`). A milestone is a release; `enhancement` is planned work, `idea` a proposal, `bug` a defect ([ADR-0021](docs/adr/0021-open-work-in-github-issues.md)).
- Direction: [docs/plan.md](docs/plan.md). How gcw works: [docs/architecture.md](docs/architecture.md). Docs carry no status: never add checklists or "done" markers to them; progress is visible only in issues, milestones and merged pull requests.
- Decisions: [docs/adr/](docs/adr/). A new decision is a new ADR plus a row in [docs/adr/README.md](docs/adr/README.md), committed with the code it concerns.
- `docs/` is committed and written in English ([ADR-0014](docs/adr/0014-docs-in-repo.md)). The only exception is `docs/research.md`, a local Polish notebook excluded via `.git/info/exclude`; never commit it.

## Rules that require a new ADR to break

- **Runtime uses the standard library only.** Third-party packages are allowed in the dev group only (pytest, etc.).
- **gcw navigates, gcloud operates.** No commands that change the state of cloud resources.
- **The completion path (`gcw __complete`) never touches the network or spawns subprocesses**; it reads the cache only. Budget: < 100 ms ([ADR-0022](docs/adr/0022-tab-budget-100ms.md)). Do not add slow top-level imports; import lazily inside functions that are not on the completion path.
- **URL routes are data, not logic.** Adding a service is primarily a registry entry, and every URL template must be verified against the real console.
- **Do not import gcloud's code.** Read gcloud's files only where an ADR allows it: its INI configuration. Never read its credential files ([ADR-0023](docs/adr/0023-no-token-database-opt-in.md)); tokens come from `gcloud auth print-access-token`.

## Stack and commands

- Python >= 3.11 (`tomllib`), uv, `src/` layout.
- `uv sync` to set up the environment, `uv run pytest` to run tests, `uv run gcw …` to run the CLI.
- Tests must not use the network or the real `~/.config/gcloud`. Use a fake `CLOUDSDK_CONFIG` under `tmp_path`.

## Workflow

- **The user reviews every edit and wants to understand it.** For every file change, briefly explain (in Polish, in the chat) what you are changing, why, and how it connects to the rest of the code. Avoid large unexplained changes; split work into steps that can be read and understood one at a time.
- **Work starts from an issue.** Read it first (`gh issue view N`); its Tasks and Done when are the scope. A pull request that finishes it says `Closes #N` in its description.
- **New work becomes an issue, not a note in the docs.** Propose it as a ready-to-paste `gh issue create` command following the templates in `.github/ISSUE_TEMPLATE/` (feature: Context, Plan, Tasks, Done when; idea: Context, Proposal, Open questions).
- **Docs change together with the code.** A pull request that changes behaviour updates `README.md` and `docs/architecture.md`; one that makes a decision adds an ADR. `docs/plan.md` changes only when the direction changes.
- **Everything committed is in English**: code, identifiers, docstrings, comments, CLI messages, commit messages, docs, this file. Only the local `docs/research.md` stays in Polish.

## Commits and pull requests

- **Every change goes through a pull request into `master`**; never commit directly to `master`. Work on a branch named `<type>/<short-description>` (e.g. `feat/gcloud-config`).
- **The user runs git and gh, not the agent.** Never run `git add`, `git commit`, `git push`, branch-switching commands or `gh pr create` yourself. Instead, propose in the chat the ready-to-paste commands together with the commit message and the PR title/description, so the user can adjust them before running.
- Format: [Conventional Commits](https://www.conventionalcommits.org/), `type: description` or `type(scope): description`.
  - Types: `feat`, `fix`, `refactor`, `perf`, `test`, `docs`, `build` (packaging, dependencies, uv), `ci`, `chore`.
  - Scope is optional. Use it only when it adds information: a layer (`cli`, `context`, `cache`, `api`, `web`, `services`) or a GCP service (`run`, `sql`, …). Omit it for cross-cutting changes; never force one.
  - Description: imperative mood, lowercase, no trailing period, about 72 characters max. Mark breaking changes with `!` (e.g. `feat(cli)!: …`).
- No AI attribution: do not add `Co-Authored-By` or "Generated with" lines to commit messages or PR descriptions.
- The PR title uses the same format, because it becomes the commit message on squash merge. The PR description explains what changed and why, and how it was verified.

## ADRs

- A significant decision (a dependency, a data format, user-visible behavior, an exception to the rules above) requires a new `docs/adr/NNNN-short-title.md` based on the [template](docs/adr/template.md).
- Do not rewrite accepted ADRs. Record a new decision as a new ADR with `Status: Accepted, supersedes NNNN`, and set `Superseded by NNNN` in the old one.

## Conventions

- **English docstrings are mandatory** for every module (what it does and what it is responsible for), class, function and method, including service modules (which GCP service it covers: routes, tabs, where the resource list comes from). Style: a one-line summary; for non-trivial logic, add a description, arguments and the return value.
- Inline comments only where the code does not speak for itself.
