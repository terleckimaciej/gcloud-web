# 0021. Open work lives in GitHub issues; docs carry no status

- Status: Accepted, supersedes [0017](0017-plan-checklists-until-issues.md)
- Date: 2026-10-26

## Context

[ADR-0017](0017-plan-checklists-until-issues.md) kept milestone checklists in `plan.md` until the MVP prototype was done, and asked for a new ADR when moving open work to GitHub. The prototype is done, and the open work has been filed as issues with milestone `0.1.0`.

Checklists in markdown go stale: they are ticked by hand, and a reader cannot tell a forgotten tick from unfinished work. A visitor who opens an outdated plan sees a project that looks abandoned or confused. Keeping the same items both in the plan and in issues doubles that risk.

## Decision

### Where open work lives

- Every piece of open work is a GitHub issue. Its checklist of tasks lives in the issue, not in markdown.
- A milestone is a release (`0.1.0`, …). It holds the issues that must be closed before that release.
- Planned work without a release yet is an open issue without a milestone, labelled `enhancement`. Proposals that are not planned are labelled `idea`. Defects are `bug`.
- Issues follow one structure: Context, Plan, Tasks, Done when (`idea`: Context, Proposal). Templates in `.github/ISSUE_TEMPLATE/` give that structure.
- A pull request that finishes an issue says `Closes #N` in its description.
- No GitHub Project board while one person works on the repository; milestones and labels are enough, and a board can be added later without moving anything.

### Docs carry no status

- `docs/plan.md` describes the direction: goal, scope, what gcw deliberately does not do, and a roadmap that links to the milestone and label views on GitHub instead of listing items. It changes when the direction changes, usually with an ADR.
- `docs/architecture.md` describes how gcw works, including the console URL templates. It changes with the code, in the same pull request.
- What is done and what is open is visible only in GitHub: issues, milestones, merged pull requests, and from 0.1.0 on `CHANGELOG.md`. The milestone checklists M1–M5 are removed from the plan; their history is in the merged pull requests.
- Hand verification of console URLs is tracked in its issue, not in a status column.

## Consequences

- No document can show stale progress, because no document shows progress.
- Contributors, human or AI, start from `gh issue list`; `AGENTS.md` says so.
- Ticking tasks is done in issues, through the GitHub UI or `gh issue edit`; closing happens on merge through `Closes #N`.
- The history of the MVP milestones is reachable only through git and pull requests, which is where its details already were.
